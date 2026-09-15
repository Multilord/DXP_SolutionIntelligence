"""Explicit, bounded source sync. No SAP repository or permissions are fabricated.

SharePoint uses Graph drive delta. Other systems expose a normalized JSON export
feed configured by an administrator. Feed access is not a native SAP Notes API.
"""
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

from pydantic import BaseModel, Field

from .core import extract, now, split_sections


class ConnectorError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def fetch(url,headers=None,data=None,limit=4*1024*1024):
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme!='https' or parsed.username or parsed.password:
        raise ConnectorError('Connector URLs must use HTTPS without embedded credentials.')
    try:
        req=urllib.request.Request(url,headers=headers or {},data=data)
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=8) as response:
            raw=response.read(limit+1)
        if len(raw)>limit:raise ConnectorError('Source exceeds the connector size limit.')
        return raw
    except ConnectorError:raise
    except Exception:
        raise ConnectorError('Source request failed. Check service credentials, access, URL and size; remote details withheld.') from None


class SourceRecord(BaseModel):
    id:str=Field(min_length=1,max_length=300)
    title:str=Field(default='',max_length=300)
    content:str=Field(default='',max_length=100000)
    url:str=Field(default='',max_length=2000)
    deleted:bool=False


def ingest_records(store,connector,source_type,records):
    """Content changes invalidate old embeddings and remove old procedure linkage."""
    normalized=[SourceRecord.model_validate(row) for row in records]
    if len(normalized)>50:raise ConnectorError('A feed page must contain at most 50 records.')
    changed=0
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        for row in normalized:
            ident='SRC-'+hashlib.sha256((connector+':'+row.id).encode()).hexdigest()[:24]
            try:old=store.get('documents',ident,db)
            except KeyError:old=None
            if row.deleted:
                if old and old['status']!='deleted':
                    old.update(status='deleted',version=old['version']+1,indexed=False);store.put('documents',old,db);changed+=1
                continue
            if len(row.content.strip())<20:raise ConnectorError('Source record has too little text.')
            digest=hashlib.sha256((row.title+'\n'+row.content).encode()).hexdigest()
            if old and old.get('hash')==digest and old['status']=='published':continue
            doc=dict(id=ident,title=row.title or row.id,content=row.content,sections=split_sections(row.content),
                     source_type=source_type,source_connector=connector,source_id=row.id,source_url=row.url,
                     passport_id=None,version=old['version']+1 if old else 1,status='published',indexed=True,
                     hash=digest,synthetic=False,created_at=old['created_at'] if old else now(),updated_at=now())
            store.put('documents',doc,db);changed+=1
    return changed


FEEDS={'kb':('KB_FEED_URL','KB_FEED_TOKEN','Internal KB'),
       'tickets':('TICKET_FEED_URL','TICKET_FEED_TOKEN','Ticket'),
       'sap':('SAP_FEED_URL','SAP_FEED_TOKEN','Vendor reference')}


def configured(name):
    if name=='sharepoint':return all(os.getenv(k) for k in ('SHAREPOINT_TENANT_ID','SHAREPOINT_CLIENT_ID','SHAREPOINT_CLIENT_SECRET','SHAREPOINT_DRIVE_ID'))
    return name in FEEDS and bool(os.getenv(FEEDS[name][0]))


def public_status(store):
    states={row['id']:row for row in store.all('connectors')}
    return [dict(id=name,configured=configured(name),last_sync=states.get(name,{}).get('last_sync'),
                 has_more=states.get(name,{}).get('has_more',False),
                 adapter='Microsoft Graph drive delta' if name=='sharepoint' else 'Normalized JSON export feed') for name in [*FEEDS,'sharepoint']]


def sync(store,name):
    if not configured(name):raise ConnectorError('Source connector is not configured. Add its server-side environment values.')
    if name=='sharepoint':return sync_sharepoint(store)
    if name not in FEEDS:raise ConnectorError('Unknown connector.')
    url_key,token_key,kind=FEEDS[name]
    headers={'Accept':'application/json'}
    if os.getenv(token_key):headers['Authorization']='Bearer '+os.environ[token_key]
    try:
        payload=json.loads(fetch(os.environ[url_key],headers))
        records=payload['records']
        if not isinstance(records,list):raise ValueError()
        count=ingest_records(store,name,kind,records)
    except ConnectorError:raise
    except Exception:raise ConnectorError('Feed must contain a records array matching the documented schema.') from None
    state={'id':name,'last_sync':now(),'has_more':False}
    store.put('connectors',state)
    return {'changed':count,**state}


def sync_sharepoint(store):
    started=time.monotonic()
    tenant=urllib.parse.quote(os.environ['SHAREPOINT_TENANT_ID'],safe='')
    drive=urllib.parse.quote(os.environ['SHAREPOINT_DRIVE_ID'],safe='')
    body=urllib.parse.urlencode({'grant_type':'client_credentials','client_id':os.environ['SHAREPOINT_CLIENT_ID'],
        'client_secret':os.environ['SHAREPOINT_CLIENT_SECRET'],'scope':'https://graph.microsoft.com/.default'}).encode()
    try:
        token=json.loads(fetch(f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token',
                               {'Content-Type':'application/x-www-form-urlencoded'},body))['access_token']
        try:state=store.get('connectors','sharepoint')
        except KeyError:state={}
        scope=hashlib.sha256(drive.encode()).hexdigest()
        url=state.get('cursor') if state.get('scope')==scope else None
        url=url or f'https://graph.microsoft.com/v1.0/drives/{drive}/root/delta'
        if urllib.parse.urlparse(url).netloc!='graph.microsoft.com':raise ConnectorError('Invalid Graph continuation URL.')
        page=json.loads(fetch(url,{'Authorization':'Bearer '+token,'Prefer':'odata.maxpagesize=5'}))
        rows=page.get('value',[])
        if len(rows)>50:raise ConnectorError('Graph returned too many items for this bounded sync page.')
        records=[]
        for row in rows:
            if time.monotonic()-started>35:raise ConnectorError('Sync time budget reached. Retry this page; progress is idempotent.')
            record={'id':drive+':'+row['id']}
            if 'deleted' in row:records.append({**record,'deleted':True});continue
            if 'file' not in row:continue
            name=row.get('name','')
            if Path(name).suffix.lower() not in ('.txt','.md','.json','.csv','.pdf','.docx'):continue
            download=row.get('@microsoft.graph.downloadUrl')
            if not download:
                item=urllib.parse.quote(row['id'],safe='')
                detail=json.loads(fetch(f'https://graph.microsoft.com/v1.0/drives/{drive}/items/{item}',{'Authorization':'Bearer '+token}))
                download=detail['@microsoft.graph.downloadUrl']
            host=urllib.parse.urlparse(download).hostname or ''
            if not host.endswith('.sharepoint.com'):raise ConnectorError('Download host is outside supported SharePoint Online domains.')
            content=extract(name,fetch(download))  # Signed download URL; never forward the Graph bearer token.
            records.append({**record,'title':name,'content':content,'url':row.get('webUrl','')})
        count=ingest_records(store,'sharepoint','SharePoint',records)
        cursor=page.get('@odata.nextLink') or page.get('@odata.deltaLink')
        if not cursor:raise ConnectorError('Graph did not return a continuation token.')
        store.put('connectors',{'id':'sharepoint','scope':scope,'cursor':cursor,'last_sync':now(),'has_more':bool(page.get('@odata.nextLink'))})
        return {'changed':count,'has_more':bool(page.get('@odata.nextLink')),'last_sync':now()}
    except ConnectorError:raise
    except Exception:raise ConnectorError('SharePoint sync failed. Check application read permissions, drive ID and document format.') from None
