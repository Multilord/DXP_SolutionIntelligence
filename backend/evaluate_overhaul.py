"""Evaluate isolated synthetic fixtures. Expected labels are never passed to retrieval/AI."""
import argparse
import json
import uuid
from pathlib import Path
from . import overhaul as d
from .core import Store, now
from .config import settings

def evaluate(ai=False, cases=None):
    store=Store(Path('.runtime/evaluation/live-v2') if ai else Path('.runtime/evaluation')/uuid.uuid4().hex);d.seed(store)
    expected=json.loads(Path('test-data/overhaul/expected.json').read_text())
    reports=[]
    for case in expected:
        if cases and case['id'] not in cases:continue
        p=d.Principal('isolated-evaluator',(case['tenant'],),'reviewer',True)
        incident=d.get(store,case['id'],p,case['tenant'],'incident')
        corpus=d.rows(store,p,case['tenant'],'knowledge')
        baseline=d.rank(incident,corpus)
        applicable=sorted(baseline,key=lambda pair:(d.assess(incident,pair[1],corpus)['status']=='incompatible',-pair[0]))
        normal=lambda value:value.removeprefix('GEN-') if value.startswith('GEN-SYN-') else value
        truth={normal(x) for x in case['correct_precedent_ids']}
        hit=lambda ids:bool(truth.intersection(normal(x) for x in ids)) if truth else None
        row=dict(id=case['id'],keyword_top3=[r['id'] for _,r in baseline[:3]],rules_top3=[r['id'] for _,r in applicable[:3]])
        row.update(keyword_hit=hit(row['keyword_top3']),rules_hit=hit(row['rules_top3']))
        if ai:
            try:
                while d.index_batch(store,p,case['tenant'],settings)['remaining']:pass
                result=d.analyze(store,p,case['tenant'],case['id'],settings)
                row.update(ai_answer=result['answer_type'],answer_type_correct=result['answer_type']==case['expected_answer_type'],ai_top3=[r['id'] for r in result['candidates'][:3]],ai_hit=hit([r['id'] for r in result['candidates'][:3]]),false_applicable=result['answer_type'] in ('guided_runbook','quick_reference') and normal(result['selected_id']) not in truth)
            except Exception as error:row['ai_error']=str(error) if isinstance(error,(d.AIUnavailable,)) else type(error).__name__
        reports.append(row)
    rate=lambda key: {'hits':sum(r.get(key) is True for r in reports),'eligible_cases':sum(r.get(key) is not None for r in reports)}
    report=dict(created_at=now(),dataset='Synthetic corrected fixtures; not an enterprise benchmark',mode='Gemini live evaluation' if ai else 'Offline keyword vs applicability-rule ranking; AI NOT evaluated',case_count=len(reports),keyword_top3=rate('keyword_hit'),rules_top3=rate('rules_hit'),ai_top3=rate('ai_hit') if ai else None,false_applicable_rate=None if not ai else rate('false_applicable'),cases=reports,limitations=['Ten development cases, not held-out accuracy evidence.','Historical closures are evidence, not approved procedures; action gating is deliberately conservative.','No operational savings measured.'])
    path=Path('backend/fixtures/evaluation-live-report.json' if ai else 'backend/fixtures/evaluation-report.json');path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--ai',action='store_true');parser.add_argument('--cases',nargs='*')
    args=parser.parse_args();evaluate(args.ai,args.cases)
