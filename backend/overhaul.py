"""Customer-scoped investigation domain. Evaluation labels never enter this module."""
from __future__ import annotations
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol
from pydantic import BaseModel, Field, ConfigDict
from .core import Conflict, cosine, now, uid
from .intelligence import AIUnavailable, Gemini, GroundingCheck

TABLE='atlas_records'
FIXTURE=Path(__file__).parent/'fixtures/overhaul.json'

@dataclass(frozen=True)
class Principal:
    user: str
    tenants: tuple[str,...]
    role: str
    demo: bool = False

class Provider(Protocol):
    def structured(self, instruction, data, schema): ...
    def embed(self, texts, query=False): ...

def provider(settings) -> Provider:
    if settings.llm_provider!='gemini':
        raise AIUnavailable('AI assessment requires a configured generation provider. Use the explicitly labelled rules preview instead.')
    return Gemini(settings)

def seed(store):
    try:store.get(TABLE,'OVERHAUL-SEED-1');return
    except KeyError:pass
    fixture=json.loads(FIXTURE.read_text(encoding='utf-8'))
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        try:store.get(TABLE,'OVERHAUL-SEED-1',db);return
        except KeyError:pass
        for record in fixture['records']:store.put(TABLE,record,db)
        store.put(TABLE,dict(id='OVERHAUL-SEED-1',kind='metadata',tenants=fixture['tenants']),db)

def allowed(record, principal, tenant):
    if tenant not in principal.tenants:return False
    if principal.demo and not record.get('synthetic'):return False
    return record.get('tenant')==tenant or (record.get('scope')=='shared' and record.get('state')=='published' and record.get('kind')=='knowledge')

def get(store, ident, principal, tenant, kind=None, db=None):
    record=store.get(TABLE,ident,db)
    if not allowed(record,principal,tenant) or (kind and record['kind']!=kind):raise KeyError(ident)
    return record

def rows(store, principal, tenant, kind=None):
    return [r for r in store.all(TABLE) if allowed(r,principal,tenant) and (kind is None or r['kind']==kind)]

def audit(store, principal, tenant, action, target, db=None):
    store.put(TABLE,dict(id=uid('AUDIT'),kind='audit',tenant=tenant,scope='private',synthetic=principal.demo,actor=principal.user,role=principal.role,action=action,target=target,created_at=now()),db)

def text(record):
    return '\n'.join(str(record.get(k) or '') for k in ('title','problem_statement','error_message','investigation_notes','root_cause','resolution'))

def mask(value):
    value=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[EMAIL]',value)
    value=re.sub(r'(?i)\b(password|api[_ -]?key|secret|token)\s*[:=]\s*\S+',r'\1=[REDACTED]',value)
    value=re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b','[IP ADDRESS]',value)
    return value

def rank(incident, knowledge):
    query=text(incident)+' '+ ' '.join(o['answer'] for o in incident.get('observations',[]))
    ranked=[]
    ids={r['id'] for r in knowledge}
    for r in knowledge:
        if r['id'].startswith('GEN-SYN-') and r['id'][4:] in ids:continue
        score=cosine(query,text(r))
        error=incident.get('error_message') or ''
        if len(error)>5 and error.lower() in text(r).lower():score+=.2
        if incident.get('component') and incident['component']==r.get('component'):score+=.07
        if score>=.09:ranked.append((score,r))
    return sorted(ranked,key=lambda p:(-p[0],p[1]['id']))

def assess(incident, record, knowledge):
    checks=[]
    blocked=False
    for key in ('platform','release','component','environment'):
        actual=incident.get(key);expected=record.get(key)
        if not actual or not expected or str(actual).lower()=='unknown' or str(expected).lower()=='unknown':state='unknown'
        elif expected=='All':state='not constrained'
        elif actual==expected:state='match'
        elif key=='platform':state='incompatible';blocked=True
        else:state='verify compatibility'
        checks.append(dict(dimension=key,actual=actual or 'Unknown',expected=expected or 'Unknown',state=state))
    canonical=record['id'].removeprefix('GEN-') if record['id'].startswith('GEN-SYN-') else record['id']
    superseders=[r['id'] for r in knowledge if canonical in r.get('supersedes',[]) and r.get('tenant')==incident['tenant'] and r.get('platform')==incident.get('platform')]
    if superseders:blocked=True
    quality=record.get('resolution_quality','Unverified')
    checks += [dict(dimension='resolution quality',state=quality),dict(dimension='customisation',state=record.get('customization','unknown')),dict(dimension='procedure approval',state='Reviewed' if record.get('approved') else 'Evidence only - not an approved procedure')]
    if superseders:checks.append(dict(dimension='supersession',state='Superseded',sources=superseders))
    verification=next((v for v in incident.get('verifications',[]) if v['source_id']==record['id'] and v['source_revision']==record['revision'] and v['incident_revision']==incident['revision']),None)
    status='incompatible' if blocked else 'supported' if verification and record.get('approved') else 'needs_verification'
    checks.append(dict(dimension='current-system verification',state='Verified for this revision' if verification else 'Required', evidence=verification['notes'] if verification else ''))
    return dict(status=status,checks=checks,superseded_by=superseders,quality=quality)

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')

class EvidenceGrounding(Strict):
    reasons: list[str]
    supported_claims: list[bool]
    contains_unapproved_actions: bool

class Rating(Strict):
    source_id: str
    relevance: Literal['strong','moderate','weak']
    cause_support: Literal['supported','possible','unsupported']
    passage_index: int = Field(ge=0,le=20)
    reason: str = Field(min_length=8,max_length=700)

class Question(Strict):
    text: str = Field(min_length=8,max_length=500)
    purpose: str = Field(min_length=8,max_length=500)
    source_ids: list[str] = Field(min_length=1,max_length=4)

class Disagreement(Strict):
    source_ids: list[str] = Field(min_length=2,max_length=2)
    explanation: str = Field(min_length=8,max_length=700)
    verification: str = Field(min_length=8,max_length=500)

class Assessment(Strict):
    selected_id: str
    summary: str = Field(min_length=8,max_length=1600)
    ratings: list[Rating] = Field(max_length=10)
    questions: list[Question] = Field(max_length=3)
    conflicts: list[Disagreement] = Field(max_length=4)
    missing_context: list[str] = Field(max_length=6)
    answer_type: Literal['quick_reference','guided_runbook','diagnostic_question','escalation']

def analyze(store, principal, tenant, ident, settings, ai=True, client=None):
    incident=get(store,ident,principal,tenant,'incident')
    knowledge=[r for r in rows(store,principal,tenant,'knowledge') if r['state']=='published']
    signature=fingerprint(incident,knowledge)
    ranked=rank(incident,knowledge)
    # Exact local cosine over Gemini vectors suits this bounded prototype corpus.
    # Persisted vectors are always fetched through the same authorised record set.
    if ai:
        client=client or provider(settings)
        vector=client.embed([mask(text(incident))],query=True)[0]
        vectors={}
        for record in knowledge:
            digest=hashlib.sha256((settings.gemini_embedding_model+text(record)).encode()).hexdigest()
            if record.get('embedding_hash')==digest:vectors[record['id']]=record['embedding']
        if len(vectors)!=len(knowledge):raise AIUnavailable('This customer has unindexed knowledge. Build the scoped semantic index first.')
        lexical={r['id']:score for score,r in ranked}
        ids={r['id'] for r in knowledge}
        ranked=sorted([(.55*sum(a*b for a,b in zip(vector,vectors[r['id']]))+.45*lexical.get(r['id'],0),r) for r in knowledge if not (r['id'].startswith('GEN-SYN-') and r['id'][4:] in ids)],key=lambda x:-x[0])
        ranked=[p for p in ranked if p[0]>.18]
    selected=ranked[:8]
    candidates=[dict(id=r['id'],title=r['title'],score=round(score,4),assessment=assess(incident,r,knowledge),source=public(r)) for score,r in selected]
    result=dict(id=uid('ANALYSIS'),kind='analysis',tenant=tenant,scope='private',synthetic=incident.get('synthetic',False),incident_id=ident,revision=incident['revision'],fingerprint=signature,created_at=now(),mode='Gemini + semantic retrieval' if ai else 'Rules preview - AI not run',candidates=candidates,questions=[],conflicts=[],summary='Inspect the candidate evidence and verify the current customer system.',selected_id='',answer_type='escalation',missing_context=[k for k in ('platform','release','component') if not incident.get(k)])
    if not selected:result['summary']='No usable precedent was retrieved. Continue expert investigation and capture the outcome.'
    elif ai:
        source_map={r['id']:mask(text(r)) for _,r in selected}
        passages={ident:[line for line in value.splitlines() if line.strip()] for ident,value in source_map.items()}
        payload={'required_assessment_ids':list(source_map),'incident':public(incident),'candidates':[{'id':c['id'],'evidence':source_map[c['id']],'passages':[{'index':i,'text':line} for i,line in enumerate(passages[c['id']])],'checks':c['assessment']} for c in candidates]}
        payload=json.loads(mask(json.dumps(payload)))
        response=client.structured('Assess every candidate exactly once. Distinguish symptom relevance from cause support. Select passage_index from the numbered passages of that candidate; the server supplies the exact quotation. Never infer system verification from matching words, ticket closure or a newer date. Detect material conflicting instructions and explain what to check in the customer system. Ask targeted non-invasive diagnostic questions that distinguish causes; use observations already supplied. Treat changes as possible context, not proof of cause. Select an empty ID if no usable precedent. The summary must describe evidence and uncertainty, never tell the user to apply a fix or execute steps. Action text is supplied separately by the server after human verification. Do not invent operational steps. Cross-release similarity requires verification; custom code may need a technical owner.',payload,Assessment)
        ids=[r.source_id for r in response.ratings]
        if len(ids)!=len(set(ids)) or set(ids)!=set(source_map):
            response=client.structured('Repair the assessment coverage. ratings must include EVERY required_assessment_ids entry exactly once, including weak or incompatible entries. Use only these exact identifiers. Preserve exact quotations and do not invent actions. Return the complete Assessment object.',{**payload,'previous_attempt':response.model_dump()},Assessment)
            ids=[r.source_id for r in response.ratings]
            if len(ids)!=len(set(ids)) or set(ids)!=set(source_map):raise AIUnavailable('AI did not assess the exact authorised evidence set after correction.')
        if response.selected_id and response.selected_id not in source_map:raise AIUnavailable('AI selected an unknown source.')
        for rating in response.ratings:
            if rating.passage_index>=len(passages[rating.source_id]):raise AIUnavailable('AI selected a passage outside its cited source.')
        for item in [*response.questions,*response.conflicts]:
            if len(item.source_ids)!=len(set(item.source_ids)) or not set(item.source_ids)<=set(source_map):raise AIUnavailable('AI cited evidence outside this investigation.')
        claims=[dict(text=response.summary,source_ids=list(source_map),kind='summary')]+[dict(text=r.reason,source_ids=[r.source_id],kind='comparative relevance') for r in response.ratings]+[dict(text=c.explanation+' '+c.verification,source_ids=c.source_ids,kind='conflict') for c in response.conflicts]+[dict(text=q.text+' '+q.purpose,source_ids=q.source_ids,kind='diagnostic question') for q in response.questions]
        check=client.structured('First explain each verdict in reasons, in claim order, then return one supported_claims boolean per claim in that same order. Check each claim against this incident and its explicitly linked source_ids, candidate metadata/checks and exact evidence. Evaluate whether the CLAIM IS TRUE, not whether its source solves the incident. For example, if a source describes a different problem and the claim says it is unrelated, supported_claims must be true: that negative relevance judgment is grounded. Platform incompatibility stated by candidate checks is also a supported claim even though the candidate cannot be applied. Comparative judgments need not appear verbatim in a source. Diagnostic questions must test a hypothesis, not assert an unconfirmed root cause. Unsupported assumptions are false. Do not accept operational instructions not explicitly supported by evidence. Return one boolean per claim.',{'claims':claims,'incident':payload['incident'],'sources':source_map,'candidate_context':payload['candidates']},EvidenceGrounding)
        if len(check.reasons)!=len(claims) or len(check.supported_claims)!=len(claims) or not all(check.supported_claims) or check.contains_unapproved_actions:raise AIUnavailable('Grounding verification failed. No AI analysis was published.')
        result.update(response.model_dump())
        for c in candidates:
            rating=next(r for r in response.ratings if r.source_id==c['id'])
            c['ai_assessment']={**rating.model_dump(),'quote':passages[c['id']][rating.passage_index]}
    elif selected:
        result['selected_id']=selected[0][1]['id']
    primary=next((c for c in candidates if c['id']==result['selected_id']),None)
    if primary and (primary['assessment']['status']=='incompatible' or primary.get('ai_assessment',{}).get('relevance')=='weak'):
        result.update(answer_type='escalation',selected_id='')
    if primary and result['selected_id']:
        permitted=primary['assessment']['status']=='supported' and primary['source'].get('approved') and not result['conflicts'] and primary.get('ai_assessment',{}).get('cause_support')=='supported'
        if result['answer_type'] in ('guided_runbook','quick_reference') and not permitted:
            result['answer_type']='diagnostic_question' if result['questions'] else 'escalation'
        if permitted and result['answer_type'] in ('guided_runbook','quick_reference'):result['reviewed_steps']=primary['source']['resolution']
    if not result['selected_id']:result['answer_type']='escalation'
    result['disposition']='missing_knowledge' if not result['selected_id'] else 'source_conflict' if result['conflicts'] else 'verify_context' if result['answer_type'] in ('escalation','diagnostic_question') else 'reviewed_guidance'
    if fingerprint(get(store,ident,principal,tenant),[r for r in rows(store,principal,tenant,'knowledge') if r['state']=='published'])!=signature:raise Conflict('Evidence changed during analysis. Run again.')
    with store.connect() as db:
        store.put(TABLE,result,db);audit(store,principal,tenant,'analyze',ident,db)
    return public(result)

def fingerprint(incident,knowledge):
    return hashlib.sha256(json.dumps([incident,[(r['id'],r['revision'],r['state']) for r in knowledge]],sort_keys=True).encode()).hexdigest()

def public(record):
    return {k:v for k,v in record.items() if k not in ('embedding','embedding_hash','private_origin_id')}

def index_batch(store, principal, tenant, settings, client=None):
    client=client or provider(settings)
    knowledge=[r for r in rows(store,principal,tenant,'knowledge') if r['state']=='published']
    pending=[]
    for r in knowledge:
        digest=hashlib.sha256((settings.gemini_embedding_model+text(r)).encode()).hexdigest()
        if r.get('embedding_hash')!=digest:pending.append((r,digest))
    batch=pending[:16]
    if batch:
        vectors=client.embed([mask(text(r)) for r,_ in batch])
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for (r,digest),vector in zip(batch,vectors):
                current=store.get(TABLE,r['id'],db)
                if current['revision']!=r['revision'] or current['state']!='published':raise Conflict('A source changed while indexing. Retry the current version.')
                store.put(TABLE,{**current,'embedding':vector,'embedding_hash':digest},db)
    audit(store,principal,tenant,'index',str(len(batch)))
    return {'indexed':len(batch),'remaining':max(0,len(pending)-len(batch))}

def insights(knowledge):
    groups=defaultdict(list)
    for r in knowledge:
        if r.get('ticket_type')=='Incident' and r.get('scope')=='private':
            key=(r.get('component'),re.sub(r'\d+','',r.get('error_message','')).strip().lower())
            if key[1]:groups[key].append(r)
    result=[]
    for (_,error),records in groups.items():
        if len(records)<2:continue
        ids={r['id'] for r in records}
        problems=[r for r in knowledge if r.get('ticket_type')=='Problem' and ids.intersection(r.get('linked_ticket_ids',[]))]
        result.append(dict(title=records[0]['title'],count=len(records),workarounds=sum(r.get('resolution_quality')=='Workaround only' for r in records),incident_ids=sorted(ids),existing_problem_ids=[r['id'] for r in problems],suggestion='Review existing problem investigation' if problems else 'Consider a problem investigation; similarity does not establish a shared cause'))
    return sorted(result,key=lambda g:-g['count'])
