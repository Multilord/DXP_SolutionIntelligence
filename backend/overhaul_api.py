"""Versioned API; caller-selected tenants never grant membership."""
import hmac
import json
import os
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from . import overhaul as domain
from .core import Conflict, now, uid

router=APIRouter(prefix='/api/v2')

def services():
    from .app import store, settings
    return store,settings

def principal(authorization: str=Header(default=''), x_demo_customer: str=Header(default=''), x_demo_role: str=Header(default='consultant')):
    credentials=os.getenv('ATLAS_ACCESS_TOKENS','')
    protected=os.getenv('ATLAS_V2_PROTECTED','').lower()=='true' or bool(credentials)
    if protected:
        try:configured=json.loads(credentials or '{}')
        except ValueError:raise HTTPException(503,'Server access configuration is invalid.')
        token=authorization.removeprefix('Bearer ')
        for secret,identity in configured.items():
            if len(secret)>=32 and authorization.startswith('Bearer ') and hmac.compare_digest(secret,token):
                return domain.Principal(identity['user'],tuple(identity['tenants']),identity['role'])
        raise HTTPException(401,'Provide a valid access token. Customer and role are assigned by the server.')
    # This mode only exposes explicitly synthetic v2 records. It is not authentication.
    fixture=json.loads(domain.FIXTURE.read_text(encoding='utf-8'))
    tenant=x_demo_customer or fixture['tenants'][0]
    if tenant not in fixture['tenants'] or x_demo_role not in ('consultant','reviewer','admin'):raise HTTPException(403,'Unknown synthetic demo context.')
    return domain.Principal('demo-'+x_demo_role,(tenant,),x_demo_role,True)

def scope(p,tenant):
    if tenant not in p.tenants:raise HTTPException(403,'Account is not assigned to this identity.')

def reviewer(p):
    if p.role not in ('reviewer','admin'):raise HTTPException(403,'A reviewer role is required.')

def setup():
    store,settings=services();domain.seed(store);return store,settings

@router.get('/session')
def session(p=Depends(principal)):
    fixture=json.loads(domain.FIXTURE.read_text(encoding='utf-8'))
    return dict(user=p.user,role=p.role,demo=p.demo,tenants=fixture['tenants'] if p.demo else p.tenants,notice='Synthetic demo: account and role switching is simulated.' if p.demo else 'Server-enforced account membership and roles; enterprise SSO is not yet connected.')

@router.get('/evaluation')
def evaluation(p=Depends(principal)):
    reviewer(p)
    path=domain.FIXTURE.parent/'evaluation-report.json'
    if not path.exists():raise HTTPException(404,'Run python -m backend.evaluate_overhaul to create a report.')
    return json.loads(path.read_text(encoding='utf-8'))

@router.get('/workspace')
def workspace(tenant:str,p=Depends(principal)):
    scope(p,tenant);store,settings=setup()
    records=domain.rows(store,p,tenant)
    kinds={k:[domain.public(r) for r in records if r['kind']==k] for k in ('incident','knowledge','draft','outcome','audit')}
    if p.role=='consultant':kinds['audit']=[]
    return {**kinds,'insights':domain.insights(kinds['knowledge']),'provider':settings.llm_provider,'synthetic_demo':p.demo}

@router.get('/records/{ident}')
def record(ident:str,tenant:str,p=Depends(principal)):
    scope(p,tenant);store,_=setup()
    r=domain.get(store,ident,p,tenant)
    if r['kind']=='audit':reviewer(p)
    if r['kind']=='analysis':
        incident=domain.get(store,r['incident_id'],p,tenant,'incident')
        knowledge=[k for k in domain.rows(store,p,tenant,'knowledge') if k['state']=='published']
        if r['fingerprint']!=domain.fingerprint(incident,knowledge):raise Conflict('Analysis is stale. Reanalyse the current authorised evidence.')
    return domain.public(r)

class Incident(BaseModel):
    title:str=Field(min_length=5,max_length=180)
    problem_statement:str=Field(min_length=15,max_length=8000)
    platform:str=Field(max_length=100)
    release:str=Field(max_length=100)
    component:str=Field(max_length=100)
    environment:Literal['production','test','development','unknown']='unknown'
    system_name:str=Field(default='',max_length=120)
    error_message:str=Field(default='',max_length=500)
    customization:Literal['present','absent','unknown']='unknown'

@router.post('/incidents',status_code=201)
def create(body:Incident,tenant:str,p=Depends(principal)):
    scope(p,tenant);store,_=setup()
    r=dict(id=uid('CASE'),kind='incident',tenant=tenant,scope='private',synthetic=p.demo,state='open',revision=1,observations=[],changes=[],created_at=now(),**body.model_dump())
    with store.connect() as db:
        store.put(domain.TABLE,r,db);domain.audit(store,p,tenant,'create_incident',r['id'],db)
    return r

class Analyze(BaseModel):
    revision:int
    mode:Literal['ai','rules']='ai'

@router.post('/incidents/{ident}/analyze')
def analyze(ident:str,body:Analyze,tenant:str,p=Depends(principal)):
    scope(p,tenant);store,settings=setup()
    r=domain.get(store,ident,p,tenant,'incident')
    if r['revision']!=body.revision:raise Conflict('Incident changed. Refresh before analyzing.')
    return domain.analyze(store,p,tenant,ident,settings,ai=body.mode=='ai')

@router.post('/index')
def index(tenant:str,p=Depends(principal)):
    scope(p,tenant);reviewer(p);store,settings=setup()
    return domain.index_batch(store,p,tenant,settings)

class Observation(BaseModel):
    revision:int
    question:str=Field(min_length=3,max_length=500)
    answer:str=Field(min_length=2,max_length=2000)

@router.post('/incidents/{ident}/observations')
def observe(ident:str,body:Observation,tenant:str,p=Depends(principal)):
    scope(p,tenant);store,_=setup()
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        r=domain.get(store,ident,p,tenant,'incident',db)
        if r['revision']!=body.revision:raise Conflict('Incident changed; refresh before saving.')
        r['observations'].append(dict(question=body.question,answer=body.answer,actor=p.user,created_at=now()))
        r['revision']+=1
        store.put(domain.TABLE,r,db);domain.audit(store,p,tenant,'record_observation',ident,db)
    return r

class Change(BaseModel):
    revision:int
    event:str=Field(min_length=8,max_length=2000)
    date:str=Field(pattern=r'^\d{4}-\d{2}-\d{2}$')

@router.post('/incidents/{ident}/changes')
def change(ident:str,body:Change,tenant:str,p=Depends(principal)):
    scope(p,tenant);reviewer(p);store,_=setup()
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE');r=domain.get(store,ident,p,tenant,'incident',db)
        if r['revision']!=body.revision:raise Conflict('Incident changed; refresh before saving.')
        r['changes'].append(dict(date=body.date,event=body.event,recorded_by=p.user));r['revision']+=1
        store.put(domain.TABLE,r,db);domain.audit(store,p,tenant,'record_change',ident,db)
    return r

class Capture(BaseModel):
    title:str=Field(min_length=5,max_length=180)
    notes:str=Field(min_length=30,max_length=12000)
    resolution:str=Field(min_length=15,max_length=8000)
    validation:str=Field(min_length=15,max_length=3000)
    quality:Literal['Confirmed root cause','Verified service-request procedure','Workaround only','Unverified']
    shared:bool=False

@router.post('/incidents/{ident}/capture',status_code=201)
def capture(ident:str,body:Capture,tenant:str,p=Depends(principal)):
    scope(p,tenant);store,_=setup();r=domain.get(store,ident,p,tenant,'incident')
    # Sharing is a second review stage; draft stays private until explicitly approved.
    draft=dict(id=uid('DRAFT2'),kind='draft',tenant=tenant,scope='private',synthetic=r.get('synthetic',False),state='technical_review',revision=1,incident_id=ident,platform=r['platform'],release=r['release'],component=r['component'],environment=r.get('environment','unknown'),customization=r['customization'],created_by=p.user,created_at=now(),**body.model_dump())
    with store.connect() as db:
        store.put(domain.TABLE,draft,db);domain.audit(store,p,tenant,'capture',draft['id'],db)
    return draft

class DraftAI(domain.Strict):
    steps:list[str]=Field(min_length=1,max_length=12)
    validation:list[str]=Field(max_length=5)
    missing_information:list[str]=Field(max_length=6)

class Notes(BaseModel):
    notes:str=Field(min_length=30,max_length=12000)

@router.post('/incidents/{ident}/draft-assist')
def draft_assist(ident:str,body:Notes,tenant:str,p=Depends(principal)):
    scope(p,tenant);store,settings=setup();domain.get(store,ident,p,tenant,'incident')
    notes=domain.mask(body.notes)
    result=domain.provider(settings).structured('Extract exact contiguous excerpts from these troubleshooting notes into resolution steps and recovery validation. Do not invent steps. List missing information separately.',{'notes':notes},DraftAI)
    if any(value not in notes for value in result.steps+result.validation):raise domain.AIUnavailable('Draft extraction invented text. Review the original notes.')
    domain.audit(store,p,tenant,'draft_assist',ident)
    return result.model_dump()

class Review(BaseModel):
    revision:int
    notes:str=Field(min_length=15,max_length=3000)
    title:str=Field(min_length=5,max_length=180)
    resolution:str=Field(min_length=15,max_length=8000)
    validation:str=Field(min_length=15,max_length=3000)
    sharing_checked:bool=False

@router.post('/drafts/{ident}/review')
def review(ident:str,body:Review,tenant:str,p=Depends(principal)):
    scope(p,tenant);reviewer(p);store,_=setup()
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE');d=domain.get(store,ident,p,tenant,'draft',db)
        if d['revision']!=body.revision or d['state']=='published':raise Conflict('Draft changed or already published.')
        d.update(title=body.title,resolution=body.resolution,validation=body.validation,revision=d['revision']+1)
        if d['state']=='technical_review' and d['shared']:
            d.update(state='sharing_review',technical_reviewer=p.user,technical_review_notes=body.notes)
        else:
            if d['shared'] and not body.sharing_checked:raise HTTPException(422,'Explicit generalisation and sharing review is required.')
            content='\n'.join([body.title,body.resolution,body.validation])
            if d['shared']:
                # Conservative detector complements, never replaces, human sharing review.
                tenants=json.loads(domain.FIXTURE.read_text(encoding='utf-8'))['tenants']
                if any(t.casefold() in content.casefold() for t in [tenant,*tenants]) or domain.mask(content)!=content:
                    raise HTTPException(422,'Remove customer identifiers or sensitive values before sharing.')
            knowledge=dict(id=uid('KNOW'),kind='knowledge',tenant=None if d['shared'] else tenant,scope='shared' if d['shared'] else 'private',synthetic=d['synthetic'],title=body.title,problem_statement=body.title,resolution=body.resolution,validation=body.validation,resolution_quality=d['quality'],environment='unknown' if d['shared'] else d.get('environment','unknown'),platform=d['platform'],release=d['release'],component=d['component'],customization='unknown' if d['shared'] else d['customization'],state='published',revision=1,approved=True,reviewed_at=now(),review_basis='Human technical and sharing review' if d['shared'] else 'Human technical review',private_origin_id=ident,linked_ticket_ids=[])
            store.put(domain.TABLE,knowledge,db);d.update(state='published',published_id=knowledge['id'])
        store.put(domain.TABLE,d,db);domain.audit(store,p,tenant,'review_'+d['state'],ident,db)
    return d

class Outcome(BaseModel):
    status:Literal['confirmed','failed','unknown']
    notes:str=Field(min_length=10,max_length=3000)
    source_id:str

@router.post('/incidents/{ident}/outcomes')
def outcome(ident:str,body:Outcome,tenant:str,p=Depends(principal)):
    scope(p,tenant);store,_=setup();r=domain.get(store,ident,p,tenant,'incident');source=domain.get(store,body.source_id,p,tenant,'knowledge')
    row=dict(id=uid('OUTCOME2'),kind='outcome',tenant=tenant,scope='private',synthetic=r.get('synthetic',False),incident_id=ident,source_revision=source['revision'],created_at=now(),actor=p.user,**body.model_dump())
    with store.connect() as db:
        store.put(domain.TABLE,row,db);domain.audit(store,p,tenant,'outcome_'+body.status,ident,db)
    return row

class Verification(BaseModel):
    revision:int
    source_id:str
    notes:str=Field(min_length=20,max_length=3000)

@router.post('/incidents/{ident}/verify')
def verify(ident:str,body:Verification,tenant:str,p=Depends(principal)):
    scope(p,tenant);reviewer(p);store,_=setup()
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE');r=domain.get(store,ident,p,tenant,'incident',db);source=domain.get(store,body.source_id,p,tenant,'knowledge',db)
        if r['revision']!=body.revision:raise Conflict('Incident changed; refresh before verification.')
        a=domain.assess(r,source,domain.rows(store,p,tenant,'knowledge'))
        if a['status']=='incompatible':raise Conflict('Cannot override incompatible or superseded evidence. Revise the procedure.')
        if not source.get('approved'):raise Conflict('Historical evidence is not an approved procedure. Capture and review a procedure first.')
        r['revision']+=1
        r.setdefault('verifications',[]).append(dict(source_id=source['id'],source_revision=source['revision'],incident_revision=r['revision'],notes=body.notes,reviewer=p.user,created_at=now()))
        store.put(domain.TABLE,r,db);domain.audit(store,p,tenant,'verify_current_system',ident,db)
    return r

class ImpactItem(domain.Strict):
    source_id:str
    quote:str=Field(min_length=8,max_length=1000)
    reason:str=Field(min_length=8,max_length=800)
    check:str=Field(min_length=8,max_length=500)

class Impact(domain.Strict):
    affected:list[ImpactItem]=Field(max_length=12)

class Cluster(domain.Strict):
    title:str=Field(min_length=5,max_length=180)
    reason:str=Field(min_length=10,max_length=800)
    incident_ids:list[str]=Field(min_length=2,max_length=40)

class Clusters(domain.Strict):
    groups:list[Cluster]=Field(max_length=15)

@router.post('/clusters')
def clusters(tenant:str,p=Depends(principal)):
    scope(p,tenant);store,settings=setup()
    candidates=[r for r in domain.rows(store,p,tenant) if r.get('scope')=='private' and (r['kind']=='incident' or r['kind']=='knowledge' and r.get('ticket_type')=='Incident')]
    if len(candidates)>60:raise HTTPException(422,'Select a smaller corpus: this prototype supports 60 private incidents per clustering request.')
    sources={r['id']:domain.mask(domain.text(r)) for r in candidates}
    client=domain.provider(settings)
    response=client.structured('Group repeated incidents or recurring workaround closures within this single customer. Include at least two incident IDs per group. Use each incident at most once; leave unrelated cases ungrouped. Explain shared evidence without declaring a common root cause. Do not recommend operational actions.',{'incidents':sources},Clusters)
    seen=[]
    for group in response.groups:seen.extend(group.incident_ids)
    if len(seen)!=len(set(seen)) or not set(seen)<=set(sources):raise domain.AIUnavailable('Clustering returned duplicate or inaccessible incidents.')
    check=client.structured('Verify each proposed grouping rationale against its incident evidence. A common symptom can justify investigation but not a confirmed common cause.',{'claims':[g.reason for g in response.groups],'groups':[{'reason':g.reason,'evidence':{i:sources[i] for i in g.incident_ids}} for g in response.groups]},domain.GroundingCheck)
    if len(check.supported_claims)!=len(response.groups) or not all(check.supported_claims) or check.contains_unapproved_actions:raise domain.AIUnavailable('Clustering grounding failed.')
    domain.audit(store,p,tenant,'cluster_incidents',str(len(seen)))
    return dict(groups=sorted([{**g.model_dump(),'count':len(g.incident_ids)} for g in response.groups],key=lambda g:-g['count']),ungrouped=len(sources)-len(seen),notice='AI grouping suggestions only. No incident was merged, closed or assigned.')

@router.post('/incidents/{ident}/impact')
def impact(ident:str,tenant:str,p=Depends(principal)):
    scope(p,tenant);reviewer(p);store,settings=setup();incident=domain.get(store,ident,p,tenant,'incident')
    if not incident.get('changes'):raise HTTPException(422,'Record a system change first.')
    knowledge=[r for r in domain.rows(store,p,tenant,'knowledge') if r['state']=='published' and r.get('platform') in (incident['platform'],'All')]
    sources={r['id']:domain.mask(domain.text(r)) for _,r in domain.rank(incident,knowledge)[:12]}
    client=domain.provider(settings)
    response=client.structured('Suggest potentially affected knowledge using only the recorded changes and exact source excerpts. Quote verbatim. Do not declare anything safe, invalid or obsolete. Every suggestion requires expert review. Absence from the bounded candidate set is not a complete impact assessment.',{'changes':incident['changes'],'sources':sources},Impact)
    for item in response.affected:
        if item.source_id not in sources or item.quote not in sources[item.source_id]:raise domain.AIUnavailable('Impact suggestion cited unsupported evidence.')
    check=client.structured('Check each suggested impact reason is supported as a possibility by the change details and source. Reject asserted causality or operational changes.',{'claims':[i.reason for i in response.affected],'changes':incident['changes'],'sources':sources},domain.GroundingCheck)
    if len(check.supported_claims)!=len(response.affected) or not all(check.supported_claims) or check.contains_unapproved_actions:raise domain.AIUnavailable('Impact grounding failed.')
    if domain.get(store,ident,p,tenant)['revision']!=incident['revision']:raise Conflict('Change context changed during assessment.')
    domain.audit(store,p,tenant,'impact_assessment',ident)
    return dict(**response.model_dump(),expert_review_required=True,candidates_considered=len(sources),total_eligible=len(knowledge),notice='Bounded suggestions, not an exhaustive change audit. No procedure status was changed.')

class ImportItem(BaseModel):
    external_id:str=Field(min_length=1,max_length=100)
    title:str=Field(min_length=5,max_length=180)
    content:str=Field(min_length=20,max_length=20000)
    platform:str=Field(max_length=100)
    release:str=Field(max_length=100)
    component:str=Field(default='',max_length=100)
    source:str=Field(min_length=2,max_length=100)

class ImportBatch(BaseModel):
    records:list[ImportItem]=Field(min_length=1,max_length=50)

@router.post('/imports')
def ingest(body:ImportBatch,tenant:str,p=Depends(principal)):
    scope(p,tenant)
    if p.role!='admin':raise HTTPException(403,'Administrator access is required.')
    store,_=setup()
    import hashlib
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        for item in body.records:
            ident='IMPORT-'+hashlib.sha256(json.dumps([tenant,item.source,item.external_id]).encode()).hexdigest()[:24]
            try:previous=store.get(domain.TABLE,ident,db)
            except KeyError:previous={}
            content=domain.mask(item.content)
            row=dict(id=ident,kind='knowledge',tenant=tenant,scope='private',synthetic=p.demo,state='published',revision=previous.get('revision',0)+1,title=domain.mask(item.title),problem_statement=content,resolution='',resolution_quality='Unverified',platform=item.platform,release=item.release,component=item.component,source=item.source,external_id=item.external_id,customization='unknown',approved=False,created_at=now(),masking_status='Basic pattern masking only; human review required before sharing',linked_ticket_ids=[])
            store.put(domain.TABLE,row,db)
        domain.audit(store,p,tenant,'import',str(len(body.records)),db)
    return dict(imported=len(body.records),notice='Private evidence only. Build embeddings before AI retrieval. No procedure approved.')

class Retract(BaseModel):
    revision:int
    reason:str=Field(min_length=10,max_length=1000)

@router.post('/knowledge/{ident}/retract')
def retract(ident:str,body:Retract,tenant:str,p=Depends(principal)):
    scope(p,tenant)
    if p.role!='admin':raise HTTPException(403,'Administrator access is required.')
    store,_=setup()
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE');r=domain.get(store,ident,p,tenant,'knowledge',db)
        if r['scope']=='shared':raise HTTPException(403,'Shared-library governance requires a separate operator workflow.')
        if r['revision']!=body.revision:raise Conflict('Source changed; refresh before retracting.')
        r.update(state='withdrawn',revision=r['revision']+1,withdrawal_reason=body.reason)
        store.put(domain.TABLE,r,db);domain.audit(store,p,tenant,'retract_source',ident,db)
    return {'status':'withdrawn'}
