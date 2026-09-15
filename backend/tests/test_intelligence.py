import unittest
import uuid
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from backend.config import settings
from backend.core import Store, Conflict
from backend.intelligence import (AIUnavailable, Gemini, Understanding, Synthesis, Selection, GroundingCheck,
                                  index_batch, index_status, retrieve, run_intelligence, DIMENSIONS)


class FakeGemini:
    """Orchestration fixture, not a semantic quality benchmark."""
    def embed(self,texts,query=False):
        return [[1.0]+[0.0]*(DIMENSIONS-1) for _ in texts]

    def structured(self,instruction,data,schema):
        if schema is Understanding:
            return Understanding(intent='guided_runbook',search_query='downstream queue dependency',symptoms=['waiting'],missing_context=[])
        if schema is GroundingCheck:
            return GroundingCheck(supported_claims=[True for _ in data['claims']],contains_unapproved_actions=False)
        candidates=data['candidates']
        candidate=next((c for c in candidates if c['id']=='PASS-QUEUE'),candidates[0] if candidates else None)
        return Selection(selected_id=candidate['id'] if candidate else '',
                         claims=[{'text':'The documented source describes this symptom.','source_ids':[candidate['source_ids'][0]]}] if candidate else [],questions=[])



class IntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.store=Store(Path('.runtime/tests')/uuid.uuid4().hex)
        self.store.seed()
        self.config=replace(settings,llm_provider='gemini',gemini_api_key='test-secret',vector_backend='local')
        self.client=FakeGemini()
        index_batch(self.store,self.config,self.client)

    def test_main_analysis_uses_ai_and_exact_source_quotes(self):
        run=run_intelligence(self.store,'SYN-1043',self.config,self.client)
        self.assertTrue(run['generation_used'])
        self.assertEqual(run['primary']['id'],'PASS-QUEUE')
        self.assertTrue(run['synthesis']['claims'][0]['citations'])
        self.assertIn('semantic',run['primary']['signals'][-1].lower())

    def test_embedding_cache_invalidates_on_source_or_model_change(self):
        self.assertEqual(index_status(self.store,self.config)['pending'],0)
        doc=self.store.get('documents','DOC-105');doc['version']+=1
        self.store.put('documents',doc)
        self.assertGreater(index_status(self.store,self.config)['pending'],0)
        with self.assertRaises(AIUnavailable):retrieve(self.store,self.config,self.client,'receiving system down')
        index_batch(self.store,self.config,self.client)
        changed=replace(self.config,gemini_embedding_model='another-model')
        self.assertEqual(index_status(self.store,changed)['indexed'],0)

    def test_unpublished_and_deleted_content_excluded(self):
        doc=self.store.get('documents','DOC-105');doc['status']='draft';self.store.put('documents',doc)
        self.assertNotIn('DOC-105',retrieve(self.store,self.config,self.client,'queue'))
        doc['status']='published';self.store.put('documents',doc)
        self.assertIn('DOC-105',retrieve(self.store,self.config,self.client,'queue'))
        doc['status']='deleted';self.store.put('documents',doc)
        self.assertNotIn('DOC-105',retrieve(self.store,self.config,self.client,'queue'))

    def test_forged_citations_are_rejected_without_persisting_answer(self):
        original=self.client.structured
        def forged(instruction,data,schema):
            value=original(instruction,data,schema)
            if schema is Selection:value.claims[0].source_ids=['INVENTED-PASSAGE']
            return value
        self.client.structured=forged
        with self.assertRaises(AIUnavailable):run_intelligence(self.store,'SYN-1043',self.config,self.client)
        self.assertEqual(self.store.all('analyses'),[])

    def test_model_cannot_select_unknown_procedure(self):
        original=self.client.structured
        def forged(instruction,data,schema):
            value=original(instruction,data,schema)
            if schema is Selection:value.selected_id='INVENTED-PROCEDURE'
            return value
        self.client.structured=forged
        with self.assertRaises(AIUnavailable):run_intelligence(self.store,'SYN-1043',self.config,self.client)

    def test_grounding_failure_is_not_published(self):
        original=self.client.structured
        def rejected(instruction,data,schema):
            if schema is GroundingCheck:return GroundingCheck(supported_claims=[False],contains_unapproved_actions=False)
            return original(instruction,data,schema)
        self.client.structured=rejected
        with self.assertRaises(AIUnavailable):run_intelligence(self.store,'SYN-1043',self.config,self.client)

    def test_incompatible_context_never_gets_executable_actions(self):
        system=self.store.get('systems','SYS-OPS');system['release']='OTHER';self.store.put('systems',system)
        run=run_intelligence(self.store,'SYN-1043',self.config,self.client)
        if run['primary']['id']=='PASS-QUEUE':self.assertEqual(run['synthesis']['action_ids'],[])
        for c in run['candidates']:
            if c['id']=='PASS-QUEUE':self.assertEqual(c['assessment']['status'],'incompatible')

    def test_missing_key_and_provider_errors_are_safe(self):
        with self.assertRaises(AIUnavailable):Gemini(replace(self.config,gemini_api_key=''))
        with patch('urllib.request.urlopen',side_effect=RuntimeError('secret-url-test-secret')):
            with self.assertRaises(AIUnavailable) as error:Gemini(self.config).embed(['test'])
        self.assertNotIn('test-secret',str(error.exception))

    def test_context_change_during_generation_rejects_result(self):
        original=self.client.structured
        def changed(instruction,data,schema):
            value=original(instruction,data,schema)
            if schema is Selection:
                incident=self.store.get('incidents','SYN-1043');incident['revision']+=1;self.store.put('incidents',incident)
            return value
        self.client.structured=changed
        with self.assertRaises(Conflict):run_intelligence(self.store,'SYN-1043',self.config,self.client)

    def test_outcomes_influence_score_only_for_procedure_version(self):
        first=run_intelligence(self.store,'SYN-1043',self.config,self.client)
        self.store.put('outcomes',{'id':'OUT-NEW','incident_id':'SYN-1043','passport_id':'PASS-QUEUE','passport_version':1,'status':'confirmed'})
        second=run_intelligence(self.store,'SYN-1043',self.config,self.client)
        self.assertGreater(second['primary']['score'],first['primary']['score'])
        self.assertEqual(second['primary']['outcome_evidence']['confirmed'],1)


if __name__=='__main__':unittest.main()
