"""Explicit setup and live checks: python -m backend.manage_ai [check|index|atlas-index|evaluate]."""
import argparse
import json
import time
from pathlib import Path

from .config import settings
from .database import create_store
from .intelligence import AIUnavailable, Gemini, Understanding, index_batch, run_intelligence


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['check','index','atlas-index','evaluate'])
    args=parser.parse_args()
    try:
        store=create_store(settings)
        store.ping()
        if args.command=='check':
            client=Gemini(settings)
            client.embed(['Synthetic support connectivity test'],query=True)
            client.structured('Classify this synthetic incident.',{'title':'A synthetic queue waits for a dependency.'},Understanding)
            result={'database':store.backend_name,'generation':'verified','embeddings':'verified','model':settings.gemini_model}
        elif args.command=='index':
            store.seed()
            result=index_batch(store,settings)
            while result['pending']:
                print(json.dumps(result))
                result=index_batch(store,settings)
        elif args.command=='atlas-index':
            if store.backend_name!='MongoDB':raise AIUnavailable('Choose DATABASE_BACKEND=mongodb for Atlas indexing.')
            result=store.ensure_vector_index(settings.vector_index)
        else:
            # Dedicated seeded database: never create evaluation incidents in the user's workspace.
            from dataclasses import replace
            from .core import Store
            import tempfile
            config=replace(settings,vector_backend='local')
            store=Store(Path(tempfile.mkdtemp(prefix='atlas-eval-')))
            store.seed()
            state=index_batch(store,config)
            while state['pending']:state=index_batch(store,config)
            cases=json.loads((Path(__file__).parents[1]/'test-data'/'ai-evaluation.json').read_text())
            rows=[]
            for number,case in enumerate(cases):
                if number:time.sleep(50)
                incident=store.get('incidents',case['seed'])
                incident.update(id=f'EVAL-{number}',title=case['query'],description=case['query'],error_code='',observations=case.get('observations',{}))
                store.put('incidents',incident)
                start=time.monotonic()
                try:
                    answer=run_intelligence(store,incident['id'],config)
                    actual=answer['primary']['id'] if answer['primary'] else None
                    passed=actual==case['expected'] and answer['answer_type']==case['answer_type']
                    rows.append({'case':number,'passed':passed,'actual':actual,'answer_type':answer['answer_type'],'seconds':round(time.monotonic()-start,2)})
                except AIUnavailable as error:rows.append({'case':number,'passed':False,'error':str(error)})
            result={'passed':sum(r['passed'] for r in rows),'total':len(rows),'cases':rows,'scope':'synthetic small-corpus evaluation; not an enterprise accuracy claim'}
        print(json.dumps(result,indent=2))
    except AIUnavailable as error:
        print(json.dumps({'status':'failed','detail':str(error)}))
        raise SystemExit(1)
    except Exception as error:
        print(json.dumps({'status':'failed','type':type(error).__name__,'detail':'Check database connectivity, permissions and index configuration; sensitive details withheld.'}))
        raise SystemExit(1)


if __name__=='__main__':main()
