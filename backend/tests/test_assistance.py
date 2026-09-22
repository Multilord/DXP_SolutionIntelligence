import unittest
import uuid
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend import app as api
from backend.assistance import (assist, latest, ResolutionDraft, ChangeImpact, GapClusters)
from backend.core import Store, Conflict, analyze
from backend.intelligence import AIUnavailable, Selection, run_intelligence, index_batch
from backend.tests.test_intelligence import FakeGemini


NOTES='The export checksum failed. Compared the export with the approved fixture. Repeated the export twice and confirmed matching checksums.'


class AssistanceClient:
    def __init__(self): self.calls=0
    def structured(self, instruction, data, schema):
        self.calls+=1
        if schema is ResolutionDraft:
            return schema(title='Verify export checksum against fixture',symptoms=['The export checksum failed.'],
                          prerequisites=[],steps=['Compared the export with the approved fixture.'],
                          validation='Repeated the export twice and confirmed matching checksums.',limitations=[],
                          missing_information=['Which fixture version was used?'])
        if schema is ChangeImpact:
            p=data['procedures'][0]['id']
            return schema(affected=[{'passport_id':p,'reason':'The recorded route update may affect the approval procedure.',
                                     'references':[{'source_id':data['change']['id']}, {'source_id':p}]}],uncertainties=['Expert verification is still required.'])
        return schema(groups=[{'title':'Export checksum investigation','gap_ids':[r['gap']['id'] for r in data['gaps']],
                               'rationale':'These incidents need further checksum investigation.'}])


class AssistanceTests(unittest.TestCase):
    def setUp(self):
        self.store=Store(Path('.runtime/tests')/uuid.uuid4().hex);self.store.seed()
        self.config=replace(api.settings,llm_provider='gemini',gemini_api_key='test',vector_backend='local',serverless=True)
        self.gap=analyze(self.store,'SYN-1044')['gap']
        self.client=AssistanceClient()

    def test_capture_is_cached_unapproved_and_context_sensitive(self):
        first=assist(self.store,self.config,'capture',self.gap['id'],NOTES,self.client)
        second=assist(self.store,self.config,'capture',self.gap['id'],NOTES,self.client)
        self.assertEqual(first['id'],second['id']);self.assertEqual(self.client.calls,1)
        self.assertEqual(self.store.all('drafts'),[])
        self.assertEqual(self.store.get('gaps',self.gap['id'])['state'],'open')
        incident=self.store.get('incidents','SYN-1044');incident['revision']+=1;self.store.put('incidents',incident)
        self.assertTrue(latest(self.store,'capture',self.gap['id'])['stale'])

    def test_capture_rejects_invented_steps(self):
        original=self.client.structured
        def forged(instruction,data,schema):
            value=original(instruction,data,schema);value.steps=['Run an invented repair command.'];return value
        self.client.structured=forged
        with self.assertRaises(AIUnavailable):assist(self.store,self.config,'capture',self.gap['id'],NOTES,self.client)
        self.assertEqual(self.store.all('assistance'),[])

    def test_capture_requires_human_confirmation_and_remains_draft(self):
        suggestion=assist(self.store,self.config,'capture',self.gap['id'],NOTES,self.client)
        body={k:suggestion['result'][k] for k in ('title','steps','validation','symptoms','prerequisites','limitations')}
        body['assistance_id']=suggestion['id']
        with patch.object(api,'store',self.store),patch.object(api,'settings',self.config):
            client=TestClient(api.app)
            self.assertEqual(client.post('/api/gaps/'+self.gap['id']+'/capture',json=body).status_code,409)
            response=client.post('/api/gaps/'+self.gap['id']+'/capture',json={**body,'human_reviewed':True})
            self.assertEqual(response.status_code,202,response.text)
            draft=response.json();self.assertEqual(draft['state'],'awaiting_review')
            self.assertEqual(draft['consultant_notes'],NOTES)
            self.assertEqual(self.store.get('passports',draft['passport_id'])['status'],'draft')

    def test_impact_cites_both_sides_without_changing_procedures(self):
        before=self.store.all('passports')
        result=assist(self.store,self.config,'impact','CHANGE-R2',client=self.client)
        self.assertEqual(result['result']['affected'][0]['state'],'expert_review_required')
        self.assertEqual(before,self.store.all('passports'))
        p=self.store.get('passports',result['result']['affected'][0]['passport_id']);p['version']+=1;self.store.put('passports',p)
        self.assertTrue(latest(self.store,'impact','CHANGE-R2')['stale'])

    def test_impact_rejects_fabricated_source(self):
        original=self.client.structured
        def forged(instruction,data,schema):
            value=original(instruction,data,schema);value.affected[0].references[0].source_id='Invented patch';return value
        self.client.structured=forged
        with self.assertRaises(AIUnavailable):assist(self.store,self.config,'impact','CHANGE-R2',client=self.client)

    def test_impact_excludes_procedures_verified_after_change(self):
        from backend.assistance import context
        data=context(self.store,'impact','CHANGE-R2')
        ids={p['id'] for p in data['procedures']}
        self.assertNotIn('PASS-ROUTE',ids)
        self.assertIn('PASS-TIMEOUT',ids)

    def test_linked_patch_version_invalidates_impact(self):
        change=self.store.get('changes','CHANGE-R2');change['document_id']='DOC-103';self.store.put('changes',change)
        assist(self.store,self.config,'impact',change['id'],client=self.client)
        doc=self.store.get('documents','DOC-103');doc['version']+=1;self.store.put('documents',doc)
        self.assertTrue(latest(self.store,'impact',change['id'])['stale'])

    def test_wire_schema_preserves_title_field_and_enforces_local_bounds(self):
        import json
        from backend.intelligence import Gemini
        gemini=Gemini(self.config)
        data=AssistanceClient().structured('',{},ResolutionDraft).model_dump()
        response={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(data)}]}}]}
        with patch.object(gemini,'request',return_value=response) as request:
            parsed=gemini.structured('test',{},ResolutionDraft)
            schema=request.call_args.args[2]['generationConfig']['responseJsonSchema']
            self.assertIn('title',schema['properties'])
            self.assertNotIn('maxItems',schema['properties']['steps'])
            self.assertEqual(parsed.title,data['title'])
        data['steps']=['Step text']*13
        response['candidates'][0]['content']['parts'][0]['text']=json.dumps(data)
        with patch.object(gemini,'request',return_value=response):
            with self.assertRaises(AIUnavailable):gemini.structured('test',{},ResolutionDraft)

    def test_clusters_preserve_records_and_compute_frequency(self):
        incident=self.store.get('incidents','SYN-1044');incident['id']='INC-SECOND';self.store.put('incidents',incident)
        self.store.put('gaps',{**self.gap,'id':'GAP-SECOND','incident_id':incident['id']})
        before=self.store.all('gaps')
        result=assist(self.store,self.config,'clusters',client=self.client)['result']
        self.assertEqual(result['coverage'],2);self.assertEqual(result['groups'][0]['frequency'],2)
        self.assertEqual(before,self.store.all('gaps'))
        gap=self.gap.copy();gap['state']='closed';self.store.put('gaps',gap)
        self.assertTrue(latest(self.store,'clusters','')['stale'])

    def test_clusters_reject_duplicate_or_missing_ids(self):
        for ids in ([self.gap['id'],self.gap['id']],['UNKNOWN']):
            with patch.object(self.client,'structured',return_value=GapClusters(groups=[{'title':'Bad grouping','gap_ids':ids,'rationale':'Invalid membership must not be saved.'}])):
                with self.assertRaises(AIUnavailable):assist(self.store,self.config,'clusters',client=self.client)

    def test_changed_context_during_generation_and_provider_failure_do_not_save(self):
        original=self.client.structured
        def changed(instruction,data,schema):
            value=original(instruction,data,schema)
            incident=self.store.get('incidents','SYN-1044');incident['revision']+=1;self.store.put('incidents',incident)
            return value
        self.client.structured=changed
        with self.assertRaises(Conflict):assist(self.store,self.config,'clusters',client=self.client)
        with patch.object(self.client,'structured',side_effect=AIUnavailable('Quota reached')):
            with self.assertRaises(AIUnavailable):assist(self.store,self.config,'clusters',client=self.client)
        self.assertEqual(self.store.all('assistance'),[])

    def test_api_routes_and_disabled_provider(self):
        with patch.object(api,'store',self.store),patch.object(api,'settings',self.config),patch('backend.assistance.Gemini',return_value=self.client):
            client=TestClient(api.app)
            self.assertEqual(client.post('/api/gaps/cluster',json={}).status_code,200)
            self.assertEqual(client.post('/api/changes/CHANGE-R2/assess-impact',json={}).status_code,200)
            self.assertEqual(client.post('/api/gaps/'+self.gap['id']+'/suggest-resolution',json={'notes':NOTES}).status_code,200)
            self.assertIsNotNone(client.get('/api/assistance/clusters').json())
        with self.assertRaises(AIUnavailable):assist(self.store,replace(self.config,llm_provider='disabled'),'clusters',client=self.client)

    def test_assistance_persists_with_mongodb_store(self):
        import mongomock
        from backend.database import MongoStore
        mongo=MongoStore(Path('.runtime/tests')/uuid.uuid4().hex,'unused','assistance_test',client=mongomock.MongoClient())
        mongo.seed()
        result=assist(mongo,self.config,'impact','CHANGE-R2',client=self.client)
        self.assertEqual(mongo.get('assistance',result['id'])['result'],result['result'])
        self.assertFalse(latest(mongo,'impact','CHANGE-R2')['stale'])

    def test_rubric_coverage_citations_and_contradictions(self):
        client=FakeGemini();index_batch(self.store,self.config,client)
        original=client.structured
        for mode in ('missing','forged','contradiction'):
            def changed(instruction,data,schema):
                value=original(instruction,data,schema)
                if schema is Selection:
                    if mode=='missing':value.assessments=[]
                    if mode=='forged':value.assessments[0].source_ids=['FAKE']
                    if mode=='contradiction':
                        for a in value.assessments:a.contradictions=['The evidence is conflicting.']
                return value
            client.structured=changed
            if mode=='contradiction':
                result=run_intelligence(self.store,'SYN-1043',self.config,client)
                self.assertEqual(result['evidence_strength'],'weak')
                self.assertEqual(result['synthesis']['action_ids'],[])
                self.assertEqual(result['answer_type'],'escalation')
            else:
                with self.assertRaises(AIUnavailable):run_intelligence(self.store,'SYN-1043',self.config,client)


if __name__=='__main__': unittest.main()
