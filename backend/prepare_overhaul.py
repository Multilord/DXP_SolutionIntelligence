"""Build runtime fixtures separately from evaluator-only labels. Originals remain untouched."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build():
    raw = json.loads((ROOT/'Overhaul/solutionatlas_synthetic_tickets.json').read_text(encoding='utf-8'))
    tenants = sorted({r['customer'] for r in raw})
    records, evaluation = [], []
    for source in raw:
        r = dict(source)
        truth = r.pop('ground_truth', None)
        r.pop('scenario_group', None)
        r['id'] = r.pop('ticket_id')
        r['kind'] = 'incident' if r.pop('dataset_role') == 'incoming_test' else 'knowledge'
        r['tenant'] = r.pop('customer')
        original_visibility = r.pop('visibility')
        r.update(scope='private', revision=1, observations=[], state='published' if r['kind']=='knowledge' else 'open', approved=False)
        r['changes'] = [{k:v for k,v in c.items() if k != 'relevant'} for c in r.pop('recent_system_changes', [])]
        r['customization'] = 'present' if r.pop('customized') or re.search(r'\b(?:custom|Z[A-Z_]+)',r['title']+' '+r['problem_statement']) else 'unknown'
        if r['ticket_type']=='Service Request': r['resolution_quality']='Verified service-request procedure'
        if r['id']=='SYN-H037': r['supersedes']=['SYN-H036']
        records.append(r)
        # Shared records are separate curated SYNTHETIC derivatives, never raw tenant tickets.
        if r['kind']=='knowledge' and original_visibility=='shared_generalized' and r['customization']!='present':
            shared = dict(r)
            shared.update(id='GEN-'+r['id'], tenant=None, scope='shared', origin='Curated synthetic generalisation', linked_ticket_ids=[])
            for key in ('title','problem_statement','investigation_notes','resolution','root_cause','error_message'):
                value=shared.get(key) or ''
                for tenant in tenants:value=value.replace(tenant,'the customer')
                value=re.sub(r'\b(?:plant|company code|sales org)\s+\d+', 'the affected organisational unit', value, flags=re.I)
                shared[key]=value
            records.append(shared)
        if truth:
            evaluation.append({'id':r['id'], 'tenant':r['tenant'], **truth})
    for ident,title,body,component in [
        ('GEN-CUSTOM-PERIOD','Custom posting validation can mimic a closed period','When standard period settings appear open, inspect approved custom validation logic and its effective dates. A technical consultant must verify whether such a rule exists before proposing a change.','FI-GL'),
        ('GEN-JOB-LOCK','Recurring job locks: investigate overlapping schedules','Repeated restarts do not establish a root cause. Compare failure timestamps, lock owners and overlapping job schedules. A scheduling dependency is only a candidate after overlap is confirmed in the current system.','BC-BMT-WFM')]:
        records.append(dict(id=ident,kind='knowledge',tenant=None,scope='shared',title=title,problem_statement=body,investigation_notes=body,resolution=body,root_cause=None,resolution_quality='Unverified',platform='All',release='All',component=component,module='FI',customization='unknown',state='published',revision=1,synthetic=True,approved=False,origin='Curated synthetic generalisation',linked_ticket_ids=[]))
    for e in evaluation:
        if e['id']=='SYN-Q03':e['correct_precedent_ids']=['GEN-CUSTOM-PERIOD','GEN-SYN-H007']
        if e['id']=='SYN-Q07':
            e['correct_precedent_ids']=['GEN-JOB-LOCK']
            e['not_applicable_lookalikes']=[]
            e['expected_flags']=['recurrence_reported','suggest_problem_investigation']
        if e['id']=='SYN-Q09':
            e['correct_precedent_ids']=['GEN-SYN-H039'];e['conditional_precedent_ids']=['GEN-SYN-H040']
        e['expected_answer_type']={'runbook':'guided_runbook'}.get(e['expected_answer_type'],e['expected_answer_type'])
    docs=json.loads((ROOT/'Overhaul/solutionatlas_synthetic_knowledge_docs.json').read_text(encoding='utf-8'))
    for d in docs:
        records.append(dict(id=d['doc_id'],kind='knowledge',tenant=d.get('customer'),scope='private' if d.get('customer') else 'shared',title=d['title'],source=d['source'],problem_statement=d['content'],resolution=d['content'],platform=d['applies_to']['platform'],release=d['applies_to']['release'],component='',module='',resolution_quality='Unverified',state='published',revision=1,synthetic=True,approved=False,last_updated=d['last_updated'],owner=d['owner'],customization='unknown',linked_ticket_ids=[]))
    target=ROOT/'backend/fixtures';target.mkdir(exist_ok=True)
    (target/'overhaul.json').write_text(json.dumps({'version':1,'tenants':tenants,'records':records},indent=2),encoding='utf-8')
    target=ROOT/'test-data/overhaul';target.mkdir(exist_ok=True)
    (target/'expected.json').write_text(json.dumps(evaluation,indent=2),encoding='utf-8')
    print(f'{len(records)} runtime records; {len(evaluation)} isolated evaluation labels')

if __name__=='__main__':build()
