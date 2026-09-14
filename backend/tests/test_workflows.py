import io
import uuid
import unittest
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient
from backend import run  # Enables the optional offline dependency cache.
from backend import app as api
from backend.core import Store, Worker, analyze, assess, extract


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        # Named workspace folders avoid Windows sandbox tempfile ACL issues.
        self.store=Store(Path('.runtime/tests')/uuid.uuid4().hex)
        self.store.seed()
        self.old_store,self.old_worker=api.store,api.worker
        api.store=self.store;api.worker=Worker(self.store)
        self.client=TestClient(api.app)

    def tearDown(self):
        self.client.close()
        api.store,api.worker=self.old_store,self.old_worker

    def post(self,path,body=None,status=200):
        response=self.client.post('/api'+path,json=body or {})
        self.assertEqual(response.status_code,status,response.text)
        return response.json()

    def test_diagnostic_then_runbook_with_evidence(self):
        result=self.post('/incidents/SYN-1042/analyze',{'revision':1})
        self.assertEqual(result['answer_type'],'diagnostic_question')
        self.assertEqual(result['primary']['id'],'PASS-ROUTE')
        self.assertTrue(result['primary']['evidence'][0]['section_id'])
        alternatives={c['id']:c['assessment']['status'] for c in result['candidates']}
        self.assertEqual(alternatives['PASS-TIMEOUT'],'needs_review')
        self.assertEqual(alternatives['PASS-EMBED'],'incompatible')
        result=self.post('/incidents/SYN-1042/observations',{'revision':1,'field':'alternate_path_works','answer':'yes'})
        self.assertEqual(result['answer_type'],'guided_runbook')
        self.assertFalse(result['generation_used'])
        self.post('/incidents/SYN-1042/observations',{'revision':1,'field':'alternate_path_works','answer':'yes'},409)

    def test_negative_observation_withholds_runbook(self):
        result=self.post('/incidents/SYN-1042/observations',{'revision':1,'field':'alternate_path_works','answer':'no'})
        self.assertEqual(result['answer_type'],'escalation')
        self.assertIsNotNone(result['gap'])

    def test_change_invalidates_result_and_revalidation_recovers(self):
        old=analyze(self.store,'SYN-1043')
        self.post('/changes',{'system_id':'SYS-OPS','label':'Mock downstream policy update'},201)
        self.assertEqual(analyze(self.store,'SYN-1043')['primary']['assessment']['status'],'needs_review')
        self.assertTrue(self.client.get('/api/recommendations/'+old['id']+'/status').json()['stale'])
        self.post('/recommendations/'+old['id']+'/explain',status=409)
        self.post('/passports/PASS-QUEUE/validate',{'system_id':'SYS-OPS','notes':'Observed a completed mock batch after checking the new dependency policy.'})
        self.assertEqual(analyze(self.store,'SYN-1043')['answer_type'],'guided_runbook')

    def test_unrelated_change_does_not_block_procedure(self):
        self.post('/changes',{'system_id':'SYS-FIN','label':'Mock finance release update'},201)
        self.assertEqual(analyze(self.store,'SYN-1043')['answer_type'],'guided_runbook')

    def test_incompatibility_cannot_be_overridden(self):
        self.post('/passports/PASS-EMBED/validate',{'system_id':'SYS-FIN','notes':'Attempted to revalidate mismatched deployment.'},409)
        self.post('/changes',{'system_id':'SYS-OPS','label':'Mock breaking protocol change','impact':'incompatible'},201)
        self.post('/passports/PASS-QUEUE/validate',{'system_id':'SYS-OPS','notes':'Attempted to revalidate known incompatible procedure.'},409)
        self.assertEqual(analyze(self.store,'SYN-1043')['primary']['assessment']['status'],'incompatible')

    def test_missing_system_history_withholds_action(self):
        system=self.store.get('systems','SYS-OPS');system['history_complete']=False;self.store.put('systems',system)
        self.assertEqual(analyze(self.store,'SYN-1043')['primary']['assessment']['status'],'unknown')

    def test_capture_index_review_publish_reuse(self):
        result=analyze(self.store,'SYN-1044');gap=result['gap']
        body={'title':'Validate the experimental export checksum','steps':['Inspect the mock export checksum configuration.','Correct the confirmed fixture mismatch with the owner.'],'validation':'Repeated the mock export and compared the checksum with the expected fixture.'}
        draft=self.post('/gaps/'+gap['id']+'/capture',body,202)
        self.assertEqual(self.post('/gaps/'+gap['id']+'/capture',body,202)['id'],draft['id'])
        self.assertEqual(analyze(self.store,'SYN-1044')['answer_type'],'escalation')
        self.post('/drafts/'+draft['id']+'/publish',status=409)
        job=next(j for j in self.store.all('jobs') if j.get('draft_id')==draft['id'])
        api.worker.process(job)
        self.assertEqual(self.store.get('drafts',draft['id'])['state'],'awaiting_review')
        self.assertEqual(analyze(self.store,'SYN-1044')['answer_type'],'escalation')
        self.post('/drafts/'+draft['id']+'/publish')
        self.post('/drafts/'+draft['id']+'/publish')
        fresh=analyze(self.store,'SYN-1044')
        self.assertEqual(fresh['answer_type'],'guided_runbook')
        self.assertEqual(fresh['primary']['id'],draft['passport_id'])
        self.assertEqual(self.store.get('gaps',gap['id'])['state'],'closed')

    def test_exact_draft_version_required(self):
        gap=analyze(self.store,'SYN-1044')['gap']
        draft=self.post('/gaps/'+gap['id']+'/capture',{'title':'Export fixture procedure','steps':['Inspect the expected fixture.'],'validation':'Verified the checksum against the expected mock fixture.'},202)
        api.worker.process(self.store.all('jobs')[0])
        doc=self.store.get('documents',draft['document_id']);doc['version']=2;self.store.put('documents',doc)
        self.post('/drafts/'+draft['id']+'/publish',status=409)

    def test_upload_deduplicates_and_is_evidence_only(self):
        content=b'FOLD_CHECKSUM_7 experimental export checksum signature. Investigate the fixture with its owner.'
        response=self.client.post('/api/uploads',files={'file':('checksum.md',content,'text/markdown')},data={'source_type':'SharePoint'})
        self.assertEqual(response.status_code,202)
        job=response.json();api.worker.process(job)
        duplicate=self.client.post('/api/uploads',files={'file':('checksum.md',content)},data={'source_type':'SharePoint'}).json()
        self.assertTrue(duplicate['duplicate'])
        result=analyze(self.store,'SYN-1044')
        self.assertEqual(result['answer_type'],'escalation')
        self.assertIsNone(result['primary']['passport'])

    def test_failed_upload_records_error(self):
        job=self.client.post('/api/uploads',files={'file':('broken.json',b'not valid json')}).json()
        api.worker.process(job)
        self.assertEqual(self.store.get('jobs',job['id'])['state'],'failed')
        self.assertEqual(self.store.get('documents',job['document_id'])['status'],'failed')

    def test_outcome_idempotency_and_failure_memory(self):
        body={'passport_id':'PASS-QUEUE','status':'failed','notes':'The mock downstream check did not restore processing.','idempotency_key':'repeat-request-1'}
        a=self.post('/incidents/SYN-1043/outcomes',body)
        b=self.post('/incidents/SYN-1043/outcomes',body)
        self.assertEqual(a['id'],b['id'])
        self.assertEqual(len(analyze(self.store,'SYN-1043')['failures']),2)

    def test_quick_reference_and_no_auth(self):
        self.assertEqual(analyze(self.store,'SYN-1045')['answer_type'],'quick_reference')
        self.assertFalse(self.client.get('/api/workspace').json()['runtime']['authentication'])

    def test_docx_extraction(self):
        content=io.BytesIO()
        with zipfile.ZipFile(content,'w') as archive:
            archive.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Example verified resolution.</w:t></w:r></w:p></w:body></w:document>')
        self.assertEqual(extract('sample.docx',content.getvalue()),'Example verified resolution.')

    def test_cross_origin_mutation_is_rejected(self):
        response=self.client.post('/api/changes',json={'system_id':'SYS-FIN','label':'Unwanted change'},headers={'origin':'https://example.com'})
        self.assertEqual(response.status_code,403)


if __name__=='__main__':unittest.main()
