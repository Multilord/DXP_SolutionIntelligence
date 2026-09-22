"""Opt-in live Gemini checks using synthetic fixtures and isolated local writes.

Run one case at a time to respect provider quotas:
  python -m backend.assistance_check --case capture
  python -m backend.assistance_check --case impact
  python -m backend.assistance_check --case clusters
  python -m backend.assistance_check --case evidence
This consumes Gemini quota. It never reads or modifies the shared MongoDB corpus.
"""
import argparse
import json
import uuid
from dataclasses import replace
from pathlib import Path

from .assistance import assist
from .config import settings
from .core import Store, analyze
from .intelligence import AIUnavailable, index_batch, run_intelligence


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',required=True,choices=['capture','impact','clusters','evidence'])
    args=parser.parse_args()
    config=replace(settings,database_backend='sqlite',vector_backend='local',serverless=False)
    store=Store(Path('.runtime/ai-upgrade-check')/uuid.uuid4().hex);store.seed()
    gap=analyze(store,'SYN-1044')['gap']
    if args.case=='clusters':
        original=store.get('incidents','SYN-1044')
        store.put('incidents',{**original,'id':'SYN-CHECKSUM-REPEAT','title':'Another export has the unexpected checksum signature'})
        store.put('gaps',{**gap,'id':'GAP-CHECKSUM-REPEAT','incident_id':'SYN-CHECKSUM-REPEAT'})
        other=store.get('incidents','SYN-1043')
        store.put('gaps',{**gap,'id':'GAP-QUEUE-REVIEW','incident_id':other['id'],'title':other['title'],'reason':'revalidation_required'})
    try:
        if args.case=='evidence':
            index_batch(store,config)
            result=run_intelligence(store,'SYN-1043',config)
            report={'case':args.case,'answer_type':result['answer_type'],
                    'selected':result['primary']['id'] if result['primary'] else None,
                    'ratings':len([c for c in result['candidates'] if c.get('evidence_assessment')]),
                    'evidence_strength':result['evidence_strength']}
        else:
            notes='The export checksum failed. Compared the export with the approved fixture. Repeated the export twice and confirmed matching checksums.'
            result=assist(store,config,args.case,gap['id'] if args.case=='capture' else 'CHANGE-R2' if args.case=='impact' else '',notes if args.case=='capture' else '')
            report={'case':args.case,'saved':True,'cached':result.get('cached',False),'result':result['result']}
        print(json.dumps(report,indent=2))
    except AIUnavailable as error:
        print(json.dumps({'case':args.case,'passed':False,'error':str(error)}))
        raise SystemExit(1)


if __name__=='__main__':main()
