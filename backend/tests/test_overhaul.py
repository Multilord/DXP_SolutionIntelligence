import json
import tempfile
import uuid
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import app as api
from backend import overhaul as d
from backend.core import Store
from backend.intelligence import AIUnavailable, GroundingCheck


class FakeProvider:
    def __init__(self, forged=False):self.payloads=[];self.forged=forged
    def embed(self,texts,query=False):return [[1.,0.] for _ in texts]
    def structured(self,instruction,data,schema):
        self.payloads.append(data)
        if schema==d.EvidenceGrounding:return d.EvidenceGrounding(reasons=['Supported by test evidence.']*len(data['claims']),supported_claims=[True]*len(data['claims']),contains_unapproved_actions=False)
        if schema==GroundingCheck:return GroundingCheck(supported_claims=[True]*len(data['claims']),contains_unapproved_actions=False)
        candidates=data['candidates']
        return d.Assessment(selected_id=candidates[0]['id'],summary='This is a possible precedent requiring system verification.',ratings=[d.Rating(source_id=c['id'],relevance='strong',cause_support='possible',passage_index=20 if self.forged else 0,reason='The source describes a potentially related incident.') for c in candidates],questions=[],conflicts=[],missing_context=[],answer_type='guided_runbook')


class OverhaulTests(unittest.TestCase):
    def setUp(self):
        self.store=Store(Path('.runtime/tests')/uuid.uuid4().hex);d.seed(self.store)
        self.tenant='Borneo Steel Sdn Bhd'
        self.p=d.Principal('test',(self.tenant,),'consultant',True)
        self.patches=[patch.object(api,'store',self.store),patch.dict('os.environ',{'ATLAS_ACCESS_TOKENS':'','ATLAS_V2_PROTECTED':'false'})]
        for p in self.patches:p.start()
        self.client=TestClient(api.app)
        self.headers={'X-Demo-Customer':self.tenant}
    def tearDown(self):
        self.client.close()
        for p in reversed(self.patches):p.stop()
    def call(self,path,body=None,role='consultant'):
        method=self.client.get if body is None else self.client.post
        return method('/api/v2'+path,params={'tenant':self.tenant},headers={**self.headers,'X-Demo-Role':role},**({'json':body} if body is not None else {}))

    def test_runtime_has_no_evaluation_labels(self):
        raw=d.FIXTURE.read_text()
        for key in ('ground_truth','correct_precedent_ids','expected_flags','scenario_group','"relevant":'):self.assertNotIn(key,raw)

    def test_private_cases_cannot_cross_accounts(self):
        self.assertEqual(self.call('/records/SYN-H008').status_code,404)
        self.assertEqual(self.call('/records/SYN-H032').status_code,404)
        body=self.call('/workspace').text
        self.assertNotIn('SYN-H032',body)
        self.assertIn('GEN-JOB-LOCK',body)

    def test_demo_cannot_read_real_data(self):
        self.store.put(d.TABLE,dict(id='REAL',kind='knowledge',tenant=self.tenant,scope='private',synthetic=False))
        self.assertEqual(self.call('/records/REAL').status_code,404)

    def test_customer_query_cannot_grant_membership(self):
        r=self.client.get('/api/v2/workspace',params={'tenant':'Aurora Foods Bhd'},headers=self.headers)
        self.assertEqual(r.status_code,403)

    def test_protected_identity_ignores_demo_role_and_customer(self):
        secret='a'*40
        with patch.dict('os.environ',{'ATLAS_ACCESS_TOKENS':json.dumps({secret:{'user':'sam','tenants':[self.tenant],'role':'consultant'}})}):
            self.assertEqual(self.call('/workspace').status_code,401)
            h={'Authorization':'Bearer '+secret,'X-Demo-Role':'admin','X-Demo-Customer':'Aurora Foods Bhd'}
            r=self.client.get('/api/v2/session',headers=h).json()
            self.assertEqual(r['role'],'consultant');self.assertEqual(r['tenants'],[self.tenant])
            self.assertEqual(self.client.get('/api/workspace',headers=h).status_code,410)
            self.assertEqual(self.client.post('/api/v2/index',params={'tenant':self.tenant},headers=h).status_code,403)

    def test_release_difference_is_uncertain_not_automatic_incompatibility(self):
        incident=d.get(self.store,'SYN-Q04',self.p,self.tenant)
        source=d.get(self.store,'GEN-SYN-H016',self.p,self.tenant)
        result=d.assess(incident,source,[])
        self.assertEqual(result['status'],'needs_verification')
        self.assertEqual(next(c for c in result['checks'] if c['dimension']=='release')['state'],'verify compatibility')

    def test_platform_mismatch_and_supersession_block(self):
        source=self.store.get(d.TABLE,'SYN-H001');incident=self.store.get(d.TABLE,'SYN-Q01')
        self.assertEqual(d.assess(incident,source,[])['status'],'incompatible')
        i=self.store.get(d.TABLE,'SYN-Q08');old=self.store.get(d.TABLE,'SYN-H036');new=self.store.get(d.TABLE,'SYN-H037')
        self.assertEqual(d.assess(i,old,[new])['superseded_by'],['SYN-H037'])

    def test_closed_workarounds_are_counted_without_other_tenants(self):
        p=d.Principal('x',('Aurora Foods Bhd',),'consultant',True)
        insights=d.insights(d.rows(self.store,p,'Aurora Foods Bhd','knowledge'))
        group=next(g for g in insights if 'SYN-H027' in g['incident_ids'])
        self.assertEqual(group['count'],5);self.assertEqual(group['workarounds'],5);self.assertIn('SYN-H032',group['existing_problem_ids'])
        self.assertFalse(d.insights(d.rows(self.store,self.p,self.tenant,'knowledge')))

    def test_ai_only_receives_authorised_sources_and_cannot_issue_unreviewed_runbook(self):
        provider=FakeProvider()
        for _ in range(5):d.index_batch(self.store,self.p,self.tenant,api.settings,provider)
        result=d.analyze(self.store,self.p,self.tenant,'SYN-Q07',api.settings,client=provider)
        prompt=json.dumps(provider.payloads)
        for forbidden in ('SYN-H032','ZFI_DAILY_UPLOAD','ground_truth','expected_flags'):self.assertNotIn(forbidden,prompt)
        self.assertEqual(result['answer_type'],'escalation');self.assertNotIn('reviewed_steps',result)

    def test_forged_quote_does_not_publish_analysis(self):
        provider=FakeProvider(True)
        for _ in range(5):d.index_batch(self.store,self.p,self.tenant,api.settings,provider)
        with self.assertRaises(AIUnavailable):d.analyze(self.store,self.p,self.tenant,'SYN-Q07',api.settings,client=provider)
        self.assertFalse(d.rows(self.store,self.p,self.tenant,'analysis'))

    def test_observation_revision_and_stale_analysis(self):
        result=self.call('/incidents/SYN-Q04/analyze',{'revision':1,'mode':'rules'}).json()
        self.assertEqual(self.call('/incidents/SYN-Q04/observations',{'revision':1,'question':'Which catalog is assigned?','answer':'The catalog is absent.'}).status_code,200)
        self.assertEqual(self.call('/incidents/SYN-Q04/observations',{'revision':1,'question':'Again?','answer':'Yes'}).status_code,409)
        self.assertEqual(self.call('/records/'+result['id']).status_code,409)

    def test_review_requires_role_and_shared_requires_second_approval(self):
        body=dict(title='Approved test procedure',notes='Inspected the configuration and tested the corrected setting.',resolution='Inspect the approved configuration before any correction.',validation='Run the approved test and confirm service recovery.',quality='Confirmed root cause',shared=True)
        draft=self.call('/incidents/SYN-Q04/capture',body).json()
        review=dict(revision=1,title=body['title'],resolution=body['resolution'],validation=body['validation'],notes='Reviewed against the recorded investigation.',sharing_checked=False)
        self.assertEqual(self.call('/drafts/'+draft['id']+'/review',review).status_code,403)
        first=self.call('/drafts/'+draft['id']+'/review',review,'reviewer').json()
        self.assertEqual(first['state'],'sharing_review')
        review['revision']=2
        self.assertEqual(self.call('/drafts/'+draft['id']+'/review',review,'reviewer').status_code,422)
        review['sharing_checked']=True
        published=self.call('/drafts/'+draft['id']+'/review',review,'reviewer').json()
        source=self.call('/records/'+published['published_id']).json()
        self.assertEqual(source['scope'],'shared');self.assertNotIn('private_origin_id',source);self.assertNotIn('notes',source)
        self.assertEqual(self.call('/drafts/'+draft['id']+'/review',review,'reviewer').status_code,409)

    def test_import_is_private_masked_and_unapproved(self):
        body={'records':[dict(external_id='1',title='Imported investigation notes',content='Contact test@example.com; password=verysecret for this synthetic example.',platform='ECC',release='Unknown',source='Test feed')]}
        self.assertEqual(self.call('/imports',body).status_code,403)
        self.assertEqual(self.call('/imports',body,'admin').status_code,200)
        row=next(r for r in self.call('/workspace').json()['knowledge'] if r['id'].startswith('IMPORT-'))
        self.assertEqual(row['scope'],'private');self.assertFalse(row['approved']);self.assertNotIn('verysecret',json.dumps(row));self.assertNotIn('test@example.com',json.dumps(row))

    def test_historical_ticket_cannot_be_verified_as_approved_procedure(self):
        r=self.call('/incidents/SYN-Q04/verify',dict(revision=1,source_id='GEN-SYN-H016',notes='Checked the current system configuration.'),'reviewer')
        self.assertEqual(r.status_code,409)

    def test_clustering_rejects_cross_customer_ids(self):
        from backend import overhaul_api as routes
        class ClusterProvider:
            def structured(self,instruction,data,schema):
                return routes.Clusters(groups=[routes.Cluster(title='Related cases',reason='Potentially related symptoms require investigation.',incident_ids=['SYN-Q04','SYN-H032'])])
        with patch.object(d,'provider',return_value=ClusterProvider()):
            response=self.call('/clusters',{})
        self.assertEqual(response.status_code,503)

    def test_private_review_verification_and_source_revision(self):
        body=dict(title='Approved private procedure',notes='Investigated and validated the customer configuration.',resolution='Inspect the approved configuration.',validation='Confirmed recovery in the current system.',quality='Confirmed root cause',shared=False)
        draft=self.call('/incidents/SYN-Q04/capture',body).json()
        reviewed=self.call('/drafts/'+draft['id']+'/review',dict(revision=1,title=body['title'],resolution=body['resolution'],validation=body['validation'],notes='Reviewed the documented validation.',sharing_checked=False),'reviewer').json()
        source=self.store.get(d.TABLE,reviewed['published_id'])
        result=self.call('/incidents/SYN-Q04/verify',dict(revision=1,source_id=source['id'],notes='Checked current system compatibility and validation.'),'reviewer')
        self.assertEqual(result.status_code,200)
        incident=result.json()
        self.assertEqual(d.assess(incident,source,[])['status'],'supported')
        source['revision']+=1
        self.assertEqual(d.assess(incident,source,[])['status'],'needs_verification')

    def test_unknown_environment_is_not_a_match(self):
        incident=self.store.get(d.TABLE,'SYN-Q04');source=self.store.get(d.TABLE,'GEN-SYN-H016')
        incident['environment']='unknown';source['environment']='unknown'
        result=d.assess(incident,source,[])
        self.assertEqual(next(c for c in result['checks'] if c['dimension']=='environment')['state'],'unknown')

if __name__=='__main__':unittest.main()
