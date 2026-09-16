"""Live Gemini + Atlas rehearsal using only bundled synthetic fixtures.

Run: python -m backend.demo_check
The shared MongoDB data and vector index are read only during this check.
Real Gemini calls consume the configured account's quota. No AI fallback.
"""
import argparse
import json
import tempfile
import time
from pathlib import Path

from pymongo import MongoClient

from .config import settings
from .core import Store, fingerprint
from .database import MongoStore
from .intelligence import AIUnavailable, Gemini, chunk_records, index_status, run_intelligence


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',nargs='+',choices=['diagnostic','runbook','knowledge_gap','quick_reference'])
    args=parser.parse_args()
    if settings.database_backend != 'mongodb' or settings.vector_backend != 'atlas':
        raise SystemExit('This rehearsal requires MongoDB and Atlas Vector Search.')
    # Do not construct MongoStore: its constructor creates database indexes.
    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=10000)
    report = {'scope':'Bundled synthetic fixtures only; live Gemini and Atlas reads; isolated writes. Not a Vercel connectivity check.', 'cases':[]}
    try:
        client.admin.command('ping')
        db = client[settings.mongodb_database]
        with tempfile.TemporaryDirectory(prefix='atlas-demo-check-') as folder:
            snapshot = Store(Path(folder))
            snapshot.seed()
            # Never load user incidents/documents. Only reuse embeddings whose content
            # hash matches the bundled fixture; copy no remote text or metadata.
            for fixture in chunk_records(snapshot,settings):
                row = db.chunks.find_one({'id':fixture['id']},{'_id':0,'embedding':1})
                if row:
                    snapshot.put('chunks',{**fixture,'embedding':row['embedding']})
            # Reuse the real Atlas query implementation without initialization writes.
            reader = object.__new__(MongoStore)
            reader.db = db
            snapshot.vector_search = reader.vector_search
            report['index'] = index_status(snapshot,settings)
            cases = [('diagnostic','SYN-1042',{},'diagnostic_question','PASS-ROUTE'),
                     ('runbook','SYN-1042',{'alternate_path_works':'yes'},'guided_runbook','PASS-ROUTE'),
                     ('knowledge_gap','SYN-1044',{},'escalation',None),
                     ('quick_reference','SYN-1045',{},'quick_reference','PASS-HANDOFF')]
            if args.cases:cases=[case for case in cases if case[0] in args.cases]
            report['expected_cases']=len(cases)
            for number,(label,seed,observations,expected,expected_id) in enumerate(cases):
                if number:
                    print('Waiting 60 seconds between scenarios to respect provider rate limits.',flush=True)
                    time.sleep(60)
                incident = snapshot.get('incidents',seed)
                incident.update(id='REHEARSAL-'+label,observations=observations,revision=1)
                snapshot.put('incidents',incident)
                start = time.monotonic()
                try:
                    result = run_intelligence(snapshot,incident['id'],settings,client=Gemini(settings))
                    primary = result.get('primary')
                    claims = result['synthesis']['claims']
                    selected = primary['id'] if primary else None
                    passed = result['answer_type']==expected and selected==expected_id and bool(result['generation_used'])
                    if primary:passed = passed and bool(claims) and all(c['citations'] for c in claims)
                    row = {'case':label,'passed':passed,'answer_type':result['answer_type'],'selected':selected,
                           'cited_claims':len(claims),'generation_used':result['generation_used'],
                           'alternatives':[{ 'id':c['id'],'status':c['assessment']['status']} for c in result['candidates'] if c is not primary]}
                    if label=='runbook':
                        before = fingerprint(snapshot,incident)
                        system = snapshot.get('systems',incident['system_id'])
                        snapshot.put('systems',{**system,'revision':system['revision']+1})
                        row['context_change_invalidates_result'] = before != fingerprint(snapshot,incident)
                        snapshot.put('systems',system)
                except AIUnavailable as error:
                    row = {'case':label,'passed':False,'error':str(error)}
                row['seconds'] = round(time.monotonic()-start,2)
                report['cases'].append(row)
                print(json.dumps(row),flush=True)
    except Exception as error:
        report['error'] = type(error).__name__+'; check connectivity/configuration. Driver details withheld.'
    finally:
        client.close()
    report['passed'] = len(report['cases'])==report.get('expected_cases',4) and all(c['passed'] for c in report['cases'])
    output = Path('.runtime/demo-check.json')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'report':str(output),'error':report.get('error')}))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':main()
