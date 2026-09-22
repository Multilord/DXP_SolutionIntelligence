"""On-demand AI assistance. Suggestions never publish knowledge or merge incidents."""
from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .core import Conflict, now
from .intelligence import AIUnavailable, Gemini


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ResolutionDraft(StrictModel):
    title: str = Field(min_length=5, max_length=180)
    symptoms: list[str] = Field(max_length=6)
    prerequisites: list[str] = Field(max_length=6)
    steps: list[str] = Field(max_length=12)
    validation: str = Field(max_length=2000)
    limitations: list[str] = Field(max_length=6)
    missing_information: list[str] = Field(max_length=6)


class Reference(StrictModel):
    source_id: str


class Impact(StrictModel):
    passport_id: str
    reason: str = Field(min_length=10, max_length=800)
    references: list[Reference] = Field(min_length=2, max_length=4)


class ChangeImpact(StrictModel):
    affected: list[Impact] = Field(max_length=20)
    uncertainties: list[str] = Field(max_length=6)


class GapGroup(StrictModel):
    title: str = Field(min_length=5, max_length=180)
    gap_ids: list[str] = Field(min_length=1, max_length=40)
    rationale: str = Field(min_length=10, max_length=800)


class GapClusters(StrictModel):
    groups: list[GapGroup] = Field(max_length=40)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def context(store, kind, target, notes=''):
    if kind == 'capture':
        gap = store.get('gaps', target)
        if gap['state'] != 'open':
            raise Conflict('This gap is no longer open for a new resolution draft.')
        incident = store.get('incidents', gap['incident_id'])
        return {'gap': gap, 'incident': incident, 'system': store.get('systems', incident['system_id']), 'notes': notes}
    if kind == 'impact':
        change = store.get('changes', target)
        system = store.get('systems', change['system_id'])
        validations = [v for v in store.all('validations') if v['system_id'] == system['id']]
        def predates_change(procedure):
            verified = max([v['created_at'] for v in validations
                            if v['passport_id'] == procedure['id'] and v['passport_version'] == procedure['version']
                            and v['system_revision'] == system['revision']], default=procedure.get('verified_at', ''))
            return verified < change['effective_at']
        procedures = [p for p in store.all('passports') if p['status'] == 'published'
                      and p.get('system_id') == change['system_id'] and predates_change(p)]
        if len(procedures) > 20:
            raise Conflict('Impact assessment currently supports at most 20 published procedures per system.')
        sources = {change['id']: change['label'] + '\n' + change.get('notes', '')}
        if change.get('document_id'):
            doc = store.get('documents', change['document_id'])
            if not doc.get('indexed') or doc['status'] != 'published':
                raise Conflict('The linked patch document is not published and indexed.')
            for section in doc['sections']:
                sources[f"{doc['id']}@{doc['version']}:{section['id']}"] = section['text']
        for p in procedures:
            sources[p['id']] = p['title'] + '\n' + '\n'.join(p['steps']) + '\n' + p['validation']
        if sum(map(len, sources.values())) > 60000:
            raise Conflict('Patch material is too large for one impact assessment. Use a focused patch excerpt.')
        return {'change': change, 'system': system, 'validations': validations,
                'procedures': procedures, 'sources': sources}
    if kind == 'clusters':
        gaps = sorted((g for g in store.all('gaps') if g['state'] != 'closed'), key=lambda g: g['id'])
        if len(gaps) > 40:
            raise Conflict('Clustering currently supports up to 40 unresolved gaps. No partial grouping was generated.')
        return {'gaps': [{'gap': g, 'incident': store.get('incidents', g['incident_id'])} for g in gaps]}
    raise ValueError('Unsupported assistance kind')


def snapshot(store, kind, target, payload):
    # Hash all current inputs; never reuse suggestions after source/context changes.
    return digest(context(store, kind, target, payload.get('notes', '')))


def latest(store, kind, target):
    items = [r for r in store.all('assistance') if r['kind'] == kind and r['target'] == target]
    if not items:
        return None
    record = max(items, key=lambda r: r['created_at'])
    try:
        stale = record['snapshot'] != snapshot(store, kind, target, record)
    except (Conflict, KeyError):
        stale = True
    return {**record, 'stale': stale}


def assist(store, settings, kind, target='', notes='', client=None):
    if settings.llm_provider != 'gemini':
        raise AIUnavailable('Enable Gemini to use AI assistance. No suggestion was generated.')
    data = context(store, kind, target, notes)
    stamp = digest(data)
    key = 'ASSIST-' + digest([kind, target, stamp, settings.gemini_model, 'v2'])
    try:
        return {**store.get('assistance', key), 'cached': True, 'stale': False}
    except KeyError:
        pass
    client = client or Gemini(settings)
    if kind == 'capture':
        response = client.structured(
            'Prepare a resolution draft from consultant notes. Notes describe the latest human investigation and may resolve a problem that the original incident still describes as unresolved. Title may be summarized. ALL entries in symptoms, prerequisites, steps, validation and limitations MUST be exact contiguous excerpts copied from notes. Include only actions explicitly described as performed, not proposed, attempted unsuccessfully, or negated. Put explicit recovery checks or confirmed results from the notes in validation, even if also mentioned among steps. Never invent commands, recovery, or verification. Use empty lists/empty validation only when absent from notes. Identify missing prerequisites, uncertainty or incomplete steps in missing_information; do not treat the incident original unresolved status as evidence that later verification is missing. This is an unapproved draft for human editing.',
            data, ResolutionDraft).model_dump()
        excerpts = [*response['symptoms'], *response['prerequisites'], *response['steps'], *response['limitations']]
        if response['validation']:
            excerpts.append(response['validation'])
        if any(not s.strip() or s not in notes for s in excerpts):
            raise AIUnavailable('The draft contained text not present in the consultant notes. No draft was saved.')
        if any(not 5 <= len(s) <= 1000 for s in response['steps']):
            raise AIUnavailable('The extracted steps exceed the capture limits. Use more concise notes.')
        if not response['steps']:
            response['missing_information'].append('Record the actions actually performed before submitting for review.')
        if len(response['validation'].strip()) < 20:
            response['missing_information'].append('Provide verification evidence before submitting for review.')
    elif kind == 'impact':
        response = client.structured(
            'Identify published procedures potentially affected by this change. Suggestions trigger human review only; never declare a procedure safe or obsolete. Use only supplied passport IDs. Each affected item must reference its own procedure source ID AND change or a patch-document source ID from the sources dictionary. The server supplies the exact source quotations; do not generate quote text. Explain the possible relationship, distinguishing suspicion from fact. Return affected=[] if no relationship is supported, and list uncertainties. Do not propose operational actions.',
            data, ChangeImpact).model_dump()
        allowed = {p['id'] for p in data['procedures']}
        seen = set()
        for item in response['affected']:
            ident = item['passport_id']
            refs = item['references']
            keys = {r['source_id'] for r in refs}
            if ident not in allowed or ident in seen or ident not in keys or not (keys - allowed):
                raise AIUnavailable('Impact assessment returned invalid procedure references. No assessment was saved.')
            seen.add(ident)
            if (keys & allowed) != {ident} or not keys.issubset(data['sources']):
                raise AIUnavailable('Impact assessment returned an unrelated source. No assessment was saved.')
            for reference in refs:
                reference['quote'] = data['sources'][reference['source_id']]
            item['state'] = 'expert_review_required'
    else:
        response = client.structured(
            'Group unresolved knowledge gaps by a shared problem or missing procedure, not merely the same module. Do not assert a shared root cause without evidence. Include EVERY supplied gap ID EXACTLY ONCE. Keep unrelated gaps as singletons. Explain grouping using observed symptoms and identifiers; acknowledge differing system contexts. These are suggested groups, never a merge or resolution.',
            data, GapClusters).model_dump() if data['gaps'] else {'groups': []}
        valid = {x['gap']['id']: x for x in data['gaps']}
        ids = [ident for group in response['groups'] for ident in group['gap_ids']]
        if len(ids) != len(set(ids)) or set(ids) != set(valid):
            raise AIUnavailable('Gap grouping omitted or duplicated records. No grouping was saved.')
        for group in response['groups']:
            incident_ids = sorted({valid[i]['incident']['id'] for i in group['gap_ids']})
            group.update(incident_ids=incident_ids, frequency=len(incident_ids),
                         systems=sorted({valid[i]['incident']['system_id'] for i in group['gap_ids']}))
        response['groups'].sort(key=lambda g: (-g['frequency'], g['title']))
        response['coverage'] = len(ids)
    if digest(context(store, kind, target, notes)) != stamp:
        raise Conflict('Context changed during AI assistance. Generate again.')
    return store.put('assistance', {'id': key, 'kind': kind, 'target': target, 'snapshot': stamp,
                     'notes': notes, 'result': response, 'model': settings.gemini_model,
                     'created_at': now(), 'stale': False})
