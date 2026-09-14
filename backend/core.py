"""Local, deterministic support intelligence. No external service is required."""
from __future__ import annotations

import hashlib
import io
import json
import math
import re
import sqlite3
import threading
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


TABLES = {'incidents', 'systems', 'documents', 'passports', 'changes', 'validations',
          'outcomes', 'gaps', 'drafts', 'jobs', 'analyses'}


def now():
    return datetime.now(timezone.utc).isoformat()


def uid(prefix):
    return f'{prefix}-{uuid.uuid4().hex[:10]}'


class Conflict(Exception):
    pass


class Store:
    def __init__(self, folder: Path):
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / 'atlas.sqlite3'
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            for table in TABLES:
                db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def all(self, table, db=None):
        assert table in TABLES
        if db is None:
            with self.connect() as conn:
                return self.all(table, conn)
        return [json.loads(r[0]) for r in db.execute(f'SELECT data FROM {table} ORDER BY rowid')]

    def get(self, table, ident, db=None):
        assert table in TABLES
        if db is None:
            with self.connect() as conn:
                return self.get(table, ident, conn)
        row = db.execute(f'SELECT data FROM {table} WHERE id=?', (ident,)).fetchone()
        if not row:
            raise KeyError(ident)
        return json.loads(row[0])

    def put(self, table, data, db=None):
        assert table in TABLES
        if db is None:
            with self.connect() as conn:
                return self.put(table, data, conn)
        db.execute(f'INSERT INTO {table}(id,data) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',
                   (data['id'], json.dumps(data)))
        return data

    def seed(self):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM metadata WHERE key='seeded'").fetchone():
                return
            self._seed(db)
            db.execute("INSERT INTO metadata VALUES('seeded','1')")

    def _seed(self, db):
        earlier = (datetime.now(timezone.utc) - timedelta(days=75)).isoformat()
        recent = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        systems = [
            dict(id='SYS-FIN', name='Finance applications', component='FI-AP', release='DEMO-R2', deployment='Hub', revision=1, history_complete=True),
            dict(id='SYS-OPS', name='Operations integrations', component='Integration', release='DEMO-R1', deployment='Hub', revision=1, history_complete=True),
        ]
        for x in systems: self.put('systems', x, db)
        incidents = [
            dict(id='SYN-1042', title='Invoice approval times out after deployment', description='Invoice approval fails with APPROVAL_TIMEOUT after the finance deployment. The approval screen hangs, while other applications remain available.', component='FI-AP', error_code='APPROVAL_TIMEOUT', system_id='SYS-FIN', priority='High', observations={}, revision=1, state='Open'),
            dict(id='SYN-1043', title='Integration batch stalls at handoff', description='The nightly integration batch stalls with QUEUE_WAIT. Jobs remain pending at the downstream handoff. A restart was already attempted without recovery.', component='Integration', error_code='QUEUE_WAIT', system_id='SYS-OPS', priority='Medium', observations={}, revision=1, state='Open'),
            dict(id='SYN-1044', title='Export creates an unexpected checksum signature', description='The experimental export creates a violet checksum signature FOLD_CHECKSUM_7. No documented validation procedure exists for this exporter.', component='Integration', error_code='FOLD_CHECKSUM_7', system_id='SYS-OPS', priority='Medium', observations={}, revision=1, state='Open'),
            dict(id='SYN-1045', title='Where is the approved support handover template?', description='Find the support handover template and the information required for an incident handoff.', component='Integration', error_code='', system_id='SYS-OPS', priority='Low', observations={}, revision=1, state='Open'),
        ]
        for x in incidents: self.put('incidents', {**x, 'created_at': now(), 'synthetic': True}, db)
        passports = [
            dict(id='PASS-ROUTE', title='Check the approval application route', component='FI-AP', error_code='APPROVAL_TIMEOUT', system_id='SYS-FIN', deployment='Hub', release='DEMO-R2', verified_at=recent,
                 question={'field':'alternate_path_works','text':'Does approval work through the alternate application path?','why':'This separates an application-route issue from a wider approval failure.'},
                 steps=['Compare the failing path with the alternate path in the mock application.', 'Review the route configuration against the approved DEMO-R2 configuration record.', 'Have the responsible owner correct a confirmed mismatch through the approved change process.', 'Repeat the mock approval and record the result before closing the incident.'],
                 validation='The mock approval completes through the original path, and the consultant records the observed result.', route='Finance application support', answer_type='guided_runbook'),
            dict(id='PASS-TIMEOUT', title='Review the legacy approval timeout workaround', component='FI-AP', error_code='APPROVAL_TIMEOUT', system_id='SYS-FIN', deployment='Hub', release='', verified_at=earlier, question=None,
                 steps=['Inspect the timeout settings recorded in the historical case.', 'Request expert revalidation against the current deployment before considering a change.'], validation='An expert verifies that the prerequisite and procedure still fit the current environment.', route='Finance application support', answer_type='guided_runbook'),
            dict(id='PASS-EMBED', title='Embedded deployment approval repair', component='FI-AP', error_code='APPROVAL_TIMEOUT', system_id='SYS-FIN', deployment='Embedded', release='DEMO-R1', verified_at=earlier, question=None,
                 steps=['Review the embedded-deployment guide with the platform owner.'], validation='Embedded deployment prerequisites are verified.', route='Finance application support', answer_type='guided_runbook'),
            dict(id='PASS-QUEUE', title='Inspect the downstream queue dependency', component='Integration', error_code='QUEUE_WAIT', system_id='SYS-OPS', deployment='Hub', release='DEMO-R1', verified_at=recent, question=None,
                 steps=['Read the mock batch status and identify the downstream handoff.', 'Inspect the downstream service status and collect its latest failure timestamp.', 'Give the observations to the integration owner; avoid repeating the unsuccessful restart.', 'Validate recovery by observing one completed mock batch.'], validation='A complete batch passes the handoff and the result is recorded.', route='Integration support', answer_type='guided_runbook'),
            dict(id='PASS-HANDOFF', title='Use the support handover template', component='Integration', error_code='', system_id='SYS-OPS', deployment='', release='', verified_at=recent, question=None,
                 steps=['Include the incident summary, confirmed system context, attempted actions, evidence, and outstanding questions.'], validation='The receiving owner has the evidence needed to continue investigation.', route='Service desk', answer_type='quick_reference'),
        ]
        for p in passports:
            self.put('passports', {**p, 'version':1, 'status':'published', 'owner':'Demo knowledge reviewer', 'synthetic':True}, db)
        sources = [
            ('DOC-101','DEMO-R2 approval route guide','Internal KB','PASS-ROUTE',
             'Approval timeout after deployment\nAPPROVAL_TIMEOUT in FI-AP on Hub DEMO-R2. First compare the alternate application path. If approval works there, investigate a route configuration mismatch. Review the configuration with the application owner; validate the original workflow after an approved correction. This guide describes a synthetic demonstration, not real SAP instructions.'),
            ('DOC-102','Resolved case: approval route mismatch','Ticket','PASS-ROUTE',
             'APPROVAL_TIMEOUT incident in FI-AP. Approval worked through the alternate path but timed out in the primary screen after deployment. The owner found a route mismatch in the mock application. The corrected route was verified by a completed approval. Synthetic resolved case.'),
            ('DOC-103','Historical approval timeout notes','SharePoint','PASS-TIMEOUT',
             'Historical APPROVAL_TIMEOUT workaround for FI-AP Hub deployment. The approval screen hung after a timeout. This procedure was verified before the DEMO-R2 route-policy change. It requires revalidation before reuse; later applicability has not been established. Synthetic SharePoint export.'),
            ('DOC-104','Embedded approval deployment reference','Vendor reference','PASS-EMBED',
             'APPROVAL_TIMEOUT can appear in the Embedded DEMO-R1 deployment. This repair assumes an embedded application stack. It does not apply to a Hub deployment. Synthetic vendor-style reference, not an SAP Note.'),
            ('DOC-105','Batch handoff investigation checklist','Internal KB','PASS-QUEUE',
             'Integration batch stalls with QUEUE_WAIT. Pending jobs can wait on a downstream dependency. Read the batch status, inspect the downstream service, collect timestamps, and contact Integration support. Verify one completed batch. Avoid restarting without evidence. Synthetic approved checklist.'),
            ('DOC-106','Prior unsuccessful queue restart','Ticket','PASS-QUEUE',
             'QUEUE_WAIT integration batch stalled at handoff. A restart was attempted and did not restore processing. Further investigation found the downstream dependency unavailable. This failed attempt should prevent repeated troubleshooting without new evidence. Synthetic case.'),
            ('DOC-107','Support handover template','SharePoint','PASS-HANDOFF',
             'Support handover template: include incident summary, confirmed system context, attempted actions, source evidence, and outstanding questions. Use this structure when handing an incident to the next consultant. Synthetic internal template.'),
        ]
        for ident,title,kind,passport,content in sources:
            self.put('documents', dict(id=ident,title=title,source_type=kind,passport_id=passport,content=content,
                sections=split_sections(content),version=1,status='published',indexed=True,synthetic=True,created_at=recent),db)
        self.put('changes', dict(id='CHANGE-R2',system_id='SYS-FIN',component='FI-AP',label='DEMO-R2 route-policy update',impact='unknown',effective_at=(datetime.now(timezone.utc)-timedelta(days=30)).isoformat(),recorded_at=now(),status='applied',synthetic=True),db)
        self.put('outcomes', dict(id='OUT-SEED',incident_id='SYN-1043',passport_id='PASS-QUEUE',status='failed',notes='The previous mock restart did not restore the batch. Investigate the downstream dependency before repeating it.',created_at=earlier,synthetic=True),db)


STOP = set('a an and are as at be been by can for from has have if in into is it of on or that the this to was were with after before when how what why'.split())


def tokens(text):
    return [x for x in re.findall(r'[a-z0-9_]+', text.lower()) if len(x)>1 and x not in STOP]


def cosine(a,b):
    a,b=Counter(tokens(a)),Counter(tokens(b))
    den=math.sqrt(sum(x*x for x in a.values())*sum(x*x for x in b.values()))
    return sum(v*b[k] for k,v in a.items())/den if den else 0


def split_sections(text):
    # Preserve source text and make bounded, inspectable paragraphs. No embeddings are claimed.
    chunks=[]
    for p in re.split(r'\n\s*\n',text.strip()):
        for start in range(0,len(p),1800):
            chunks.append({'id':f'section-{len(chunks)+1}','text':p[start:start+1800]})
    return chunks


def fingerprint(store, incident):
    relevant = [x for x in store.all('changes') if x['system_id']==incident['system_id']]
    body=[incident,store.get('systems',incident['system_id']),relevant,store.all('validations'),
          [(x['id'],x.get('status'),x.get('version')) for x in store.all('documents')],
          [(x['id'],x.get('status'),x.get('version')) for x in store.all('passports')],
          [x for x in store.all('outcomes') if x['incident_id']==incident['id']]]
    return hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()


def assess(passport,system,changes,validations,observations):
    checks=[]
    for field in ['component','deployment','release']:
        expected=passport.get(field)
        if not expected: continue
        actual=system.get(field)
        state='unknown' if not actual else ('match' if actual==expected else 'mismatch')
        checks.append(dict(field=field,expected=expected,actual=actual or 'Unknown',status=state))
    hard=any(x['status']=='mismatch' for x in checks)
    incomplete=any(x['status']=='unknown' for x in checks)
    valid=[v for v in validations if v['passport_id']==passport['id'] and v['system_id']==system['id'] and v['passport_version']==passport['version'] and v['system_revision']==system['revision']]
    baseline=passport.get('verified_at','') if passport.get('system_id')==system['id'] else ''
    verified=max([v['created_at'] for v in valid],default=baseline)
    applicable_changes=[c for c in changes if c['system_id']==system['id'] and c['component'] in (passport['component'],'All') and c['status']=='applied' and verified<c['effective_at']<=now()]
    incompatible=any(c['impact']=='incompatible' for c in applicable_changes)
    if hard or incompatible:
        status='incompatible'; reason='A required environment condition does not match this system.'
    elif incomplete or not system.get('history_complete') or not verified:
        status='unknown'; reason='Environment or validation history is incomplete. Verify before reuse.'
    elif applicable_changes:
        status='needs_review'; reason=f"Predates {applicable_changes[-1]['label']}. Relevant conditions need revalidation."
    else:
        status='supported'; reason='Recorded verification covers this context; no later relevant applied change is recorded.'
    question=passport.get('question')
    if status=='supported' and question:
        answer=observations.get(question['field'])
        if answer not in ('yes','no'):
            status='diagnostic';reason='One observation is needed before this procedure can be recommended.'
        elif answer=='no':
            status='needs_review';reason='The alternate path also fails. The route-only precedent does not explain the full observed scope.'
    return dict(status=status,reason=reason,checks=checks,changes=applicable_changes,verified_at=verified,question=question if status=='diagnostic' else None)


def analyze(store,ident,record_gap=True):
    incident=store.get('incidents',ident);system=store.get('systems',incident['system_id'])
    query=incident['title']+' '+incident['description']
    passports={p['id']:p for p in store.all('passports') if p['status']=='published'}
    changes=store.all('changes');validations=store.all('validations')
    candidates={}
    for doc in store.all('documents'):
        if doc['status']!='published' or not doc.get('indexed'):continue
        p=passports.get(doc.get('passport_id'))
        body=doc['title']+' '+doc['content']
        code=incident.get('error_code','').strip()
        exact=bool(code and re.search(r'(?<!\w)'+re.escape(code)+r'(?!\w)',body,re.IGNORECASE))
        overlap=set(tokens(query)) & set(tokens(body))
        similarity=cosine(query,body)
        if not exact and (similarity<.16 or len(overlap)<3): continue
        score=.65*similarity+(.3 if exact else 0)+(.05 if p and p['component']==incident['component'] else 0)
        key=p['id'] if p else doc['id']
        if key not in candidates:
            a=assess(p,system,changes,validations,incident['observations']) if p else dict(status='needs_review',reason='Relevant source found, but no reviewed procedure is linked.',checks=[],changes=[],verified_at='',question=None)
            candidates[key]=dict(id=key,title=p['title'] if p else doc['title'],passport=p,assessment=a,score=score,evidence=[],signals=[])
        candidate=candidates[key];candidate['score']=max(candidate['score'],score)
        section=max(doc['sections'],key=lambda s:cosine(query,s['text']),default={'id':'section-1','text':doc['content']})
        candidate['evidence'].append(dict(id=doc['id'],title=doc['title'],source_type=doc['source_type'],version=doc['version'],section_id=section['id'],excerpt=section['text'][:500],synthetic=doc.get('synthetic',False)))
        sig=[]
        if exact:sig.append('Exact error identifier')
        if p and p['component']==incident['component']:sig.append('Same component')
        if len(overlap)>=3:sig.append('Symptom keywords')
        candidate['signals']=list(dict.fromkeys(candidate['signals']+sig))
    ordered=sorted(candidates.values(),key=lambda c:({'supported':0,'diagnostic':1,'needs_review':2,'unknown':3,'incompatible':4}[c['assessment']['status']],-c['score']))[:6]
    primary=ordered[0] if ordered else None
    kind='escalation'
    if primary:
        status=primary['assessment']['status']
        if status=='supported':kind=primary['passport']['answer_type']
        elif status=='diagnostic':kind='diagnostic_question'
    gap=None
    if kind=='escalation' and record_gap:
        reason='no_usable_precedent' if not ordered else 'revalidation_required'
        gaps=store.all('gaps');gap=next((g for g in gaps if g['incident_id']==ident and g['state']!='closed'),None)
        if not gap:
            gap=store.put('gaps',dict(id=uid('GAP'),incident_id=ident,title=incident['title'],reason=reason,state='open',owner='Unassigned',created_at=now()))
    if primary:
        explanation=primary['assessment']['reason']
    else: explanation='No usable precedent was found in the indexed local sources. Capture a verified resolution after investigation.'
    result=dict(id=uid('RUN'),incident_id=ident,incident_revision=incident['revision'],answer_type=kind,primary=primary,candidates=ordered,explanation=explanation,gap=gap,
                generation_used=False,retrieval_mode='Local keyword + exact identifier retrieval',created_at=now(),fingerprint=fingerprint(store,incident),
                failures=[o for o in store.all('outcomes') if o['status']=='failed' and o['incident_id']==ident])
    store.put('analyses',result)
    return result


def publish(store,draft_id):
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        draft=store.get('drafts',draft_id,db)
        if draft['state']=='published':return draft
        if draft['state']!='awaiting_review':raise Conflict('Wait for indexing to complete before publishing.')
        document=store.get('documents',draft['document_id'],db)
        if not document.get('indexed') or document['version']!=draft['document_version']:
            raise Conflict('The exact draft version has not finished indexing.')
        p=store.get('passports',draft['passport_id'],db)
        p['status']='published';document['status']='published';draft['state']='published';draft['published_at']=now()
        for table,obj in [('passports',p),('documents',document),('drafts',draft)]:store.put(table,obj,db)
        gap=store.get('gaps',draft['gap_id'],db);gap['state']='closed';gap['closed_at']=now();store.put('gaps',gap,db)
        return draft


def extract(name,raw):
    ext=Path(name).suffix.lower()
    if ext in ('.txt','.md','.csv','.json'):
        text=raw.decode('utf-8-sig')
        if ext=='.json':text=json.dumps(json.loads(text),indent=2,ensure_ascii=False)
        return text
    if ext=='.pdf':
        from pypdf import PdfReader
        reader=PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:raise ValueError('Encrypted PDFs are not supported.')
        if len(reader.pages)>150:raise ValueError('Use a PDF of at most 150 pages for this prototype.')
        pages=[(i,p.extract_text() or '') for i,p in enumerate(reader.pages)]
        return '\n\n'.join(f'Page {i+1}\n'+text for i,text in pages if text.strip())
    if ext=='.docx':
        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entry=archive.getinfo('word/document.xml')
            if entry.file_size>5_000_000:raise ValueError('DOCX body exceeds the prototype extraction limit.')
            root=ET.fromstring(archive.read(entry))
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        return '\n\n'.join(''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in root.findall('.//w:p',ns))
    raise ValueError('Use Markdown, text, CSV, JSON, text PDF, or DOCX.')


class Worker:
    """One recoverable local worker. Running jobs return to queued on restart."""
    def __init__(self,store):self.store=store;self.stop=threading.Event();self.thread=None
    def start(self):
        for job in self.store.all('jobs'):
            if job['state']=='running':job['state']='queued';self.store.put('jobs',job)
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
    def close(self):
        self.stop.set()
        if self.thread:self.thread.join(timeout=3)
    def run(self):
        while not self.stop.is_set():
            for job in self.store.all('jobs'):
                if job['state']=='queued':self.process(job)
            self.stop.wait(.4)
    def process(self,job):
        try:
            job.update(state='running',stage='Extracting source text');self.store.put('jobs',job)
            if job['kind']=='upload':
                text=extract(job['filename'],(self.store.folder/job['storage_key']).read_bytes())
                if len(text.strip())<20:raise ValueError('No useful text extracted. Scanned documents require OCR, which is not enabled.')
                if len(text)>1_000_000:raise ValueError('Extracted text exceeds the prototype limit.')
                doc=self.store.get('documents',job['document_id'])
                doc.update(content=text,sections=split_sections(text),indexed=True,status='published')
                self.store.put('documents',doc)
            else:
                draft=self.store.get('drafts',job['draft_id']);doc=self.store.get('documents',draft['document_id'])
                doc.update(sections=split_sections(doc['content']),indexed=True);self.store.put('documents',doc)
                draft['state']='awaiting_review';self.store.put('drafts',draft)
                gap=self.store.get('gaps',draft['gap_id']);gap['state']='awaiting_review';self.store.put('gaps',gap)
            job.update(state='complete',stage='Indexed locally',completed_at=now())
        except Exception as e:
            job.update(state='failed',stage='Indexing failed',error=str(e)[:400])
            if job.get('document_id'):
                doc=self.store.get('documents',job['document_id']);doc['status']='failed';self.store.put('documents',doc)
            if job.get('draft_id'):
                draft=self.store.get('drafts',job['draft_id']);draft['state']='indexing_failed';self.store.put('drafts',draft)
        self.store.put('jobs',job)
