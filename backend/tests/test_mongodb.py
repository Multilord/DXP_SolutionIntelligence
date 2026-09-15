import uuid
import unittest
from pathlib import Path

import mongomock

from backend.config import Settings
from backend.core import analyze, publish
from backend.database import MongoStore


class MongoStoreTests(unittest.TestCase):
    def setUp(self):
        self.client = mongomock.MongoClient()
        self.store = MongoStore(
            Path('.runtime/tests') / uuid.uuid4().hex,
            'mongodb://unused-in-test',
            'solution_atlas_test',
            client=self.client,
        )
        self.store.seed()

    def test_seed_and_retrieval_use_mongodb_collections(self):
        self.assertEqual(self.client.solution_atlas_test.incidents.count_documents({}), 4)
        result = analyze(self.store, 'SYN-1043')
        self.assertEqual(result['answer_type'], 'guided_runbook')
        self.assertEqual(self.store.get('analyses', result['id'])['primary']['id'], 'PASS-QUEUE')

    def test_reviewed_publication_round_trip_in_mongodb(self):
        gap = analyze(self.store, 'SYN-1044')['gap']
        incident = self.store.get('incidents', gap['incident_id'])
        system = self.store.get('systems', incident['system_id'])
        passport = {
            'id':'PASS-MONGO','title':'Mongo-backed checksum procedure','component':incident['component'],
            'error_code':incident['error_code'],'system_id':system['id'],'release':system['release'],
            'deployment':system['deployment'],'verified_at':'2099-01-01T00:00:00+00:00','question':None,
            'steps':['Inspect the mock checksum fixture.'],'validation':'Observe a matching mock checksum.',
            'route':'Integration support','answer_type':'guided_runbook','version':1,'status':'draft','owner':'Test'
        }
        document = {'id':'DOC-MONGO','title':passport['title'],'source_type':'Consultant capture',
                    'passport_id':passport['id'],'content':'FOLD_CHECKSUM_7 checksum fixture validation',
                    'sections':[{'id':'section-1','text':'FOLD_CHECKSUM_7 checksum fixture validation'}],
                    'version':1,'status':'draft','indexed':True,'created_at':passport['verified_at']}
        draft = {'id':'DRAFT-MONGO','gap_id':gap['id'],'incident_id':incident['id'],
                 'passport_id':passport['id'],'document_id':document['id'],'document_version':1,
                 'title':passport['title'],'steps':passport['steps'],'validation':passport['validation'],
                 'state':'awaiting_review','created_at':passport['verified_at']}
        for table, row in [('passports',passport),('documents',document),('drafts',draft)]:
            self.store.put(table,row)
        publish(self.store,draft['id'])
        self.assertEqual(self.store.get('documents','DOC-MONGO')['status'],'published')
        self.assertEqual(self.store.get('gaps',gap['id'])['state'],'closed')

    def test_public_configuration_never_contains_secrets(self):
        config = Settings(
            'mongodb','mongodb+srv://name:secret@example','atlas',Path('.runtime/files'),
            'openai','http://localhost:11434','qwen3:4b','sk-secret','gpt-test',
            'https://sap.example','sap-id','sap-secret','tenant','sp-id','sp-secret'
        )
        status = config.public_status()
        self.assertNotIn('secret',str(status))
        self.assertTrue(status['sap_configured'])
        self.assertTrue(status['sharepoint_configured'])


if __name__ == '__main__':
    unittest.main()
