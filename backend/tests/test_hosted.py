import os
import unittest
import uuid
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch

import mongomock
from fastapi.testclient import TestClient
from backend import app as api
from backend.config import Settings, ConfigError
from backend.core import Worker, analyze
from backend.database import MongoStore


class HostedWorkflows(unittest.TestCase):
    def setUp(self):
        self.store=MongoStore(Path('.runtime/tests')/uuid.uuid4().hex,'unused','hosted_test',client=mongomock.MongoClient())
        self.store.seed()
        self.patches=[patch.object(api,'store',self.store),patch.object(api,'worker',Worker(self.store)),
                      patch.object(api,'settings',replace(api.settings,serverless=True,llm_provider='disabled')),
                      patch.dict(os.environ,{'ATLAS_ALLOWED_HOSTS':'atlas-example.vercel.app'})]
        for p in self.patches:p.start()
        self.client=TestClient(api.app)

    def tearDown(self):
        self.client.close()
        for p in reversed(self.patches):p.stop()

    def test_upload_persists_extracted_content_without_local_file(self):
        response=self.client.post('/api/uploads',files={'file':('hosted.md',b'QUEUE_WAIT: inspect the downstream dependency and retain observations.')})
        self.assertEqual(response.status_code,202,response.text)
        job=response.json()
        self.assertEqual(job['state'],'complete')
        self.assertNotIn('storage_key',job)
        self.assertEqual(list(self.store.folder.iterdir()),[])
        self.assertTrue(self.store.get('documents',job['document_id'])['indexed'])

    def test_hosted_startup_does_not_depend_on_database(self):
        from pymongo.errors import ServerSelectionTimeoutError
        with patch.object(self.store,'seed',side_effect=ServerSelectionTimeoutError('private host')):
            with TestClient(api.app) as client:
                self.assertEqual(client.get('/api/configuration').status_code,200)
        with patch.object(self.store,'ping',side_effect=ServerSelectionTimeoutError('private host')):
            response=self.client.get('/api/health')
            self.assertEqual(response.status_code,503)
            self.assertNotIn('private host',response.text)

    def test_capture_is_indexed_before_response_and_publish_reuses(self):
        gap=analyze(self.store,'SYN-1044')['gap']
        body={'title':'Hosted checksum verification','steps':['Compare the checksum with the approved mock fixture.'],
              'validation':'Repeated the mock export and observed the expected checksum.'}
        response=self.client.post('/api/gaps/'+gap['id']+'/capture',json=body)
        self.assertEqual(response.status_code,202,response.text)
        draft=response.json()
        self.assertEqual(draft['state'],'awaiting_review')
        self.assertEqual(analyze(self.store,'SYN-1044')['answer_type'],'escalation')
        self.assertEqual(self.client.post('/api/drafts/'+draft['id']+'/publish').status_code,200)
        self.assertEqual(analyze(self.store,'SYN-1044')['answer_type'],'guided_runbook')

    def test_deployed_origin_is_accepted_and_unrelated_origin_rejected(self):
        payload={'revision':1}
        self.assertEqual(self.client.post('/api/incidents/SYN-1043/analyze',json=payload,headers={'origin':'https://atlas-example.vercel.app'}).status_code,200)
        self.assertEqual(self.client.post('/api/incidents/SYN-1043/analyze',json=payload,headers={'origin':'https://unrelated.example'}).status_code,403)

    def test_upload_limit_and_failure_are_explicit(self):
        response=self.client.post('/api/uploads',files={'file':('large.txt',b'a'*(4*1024*1024+1))})
        self.assertEqual(response.status_code,413)
        failure=self.client.post('/api/uploads',files={'file':('bad.json',b'not json')}).json()
        self.assertEqual(failure['state'],'failed')

    def test_serverless_rejects_local_database_and_local_model(self):
        with patch.dict(os.environ,{'VERCEL':'1','DATABASE_BACKEND':'sqlite'},clear=True):
            with self.assertRaises(ConfigError):Settings.from_env()
        with patch.dict(os.environ,{'VERCEL':'1','DATABASE_BACKEND':'mongodb','MONGODB_URI':'mongodb://localhost:27017'},clear=True):
            with self.assertRaises(ConfigError):Settings.from_env()
        with patch.dict(os.environ,{'VERCEL':'1','DATABASE_BACKEND':'mongodb','MONGODB_URI':'mongodb+srv://cluster.example','LLM_PROVIDER':'ollama'},clear=True):
            with self.assertRaises(ConfigError):Settings.from_env()

    def test_hosted_storage_ignores_windows_local_path(self):
        with patch.dict(os.environ,{'VERCEL':'1','DATABASE_BACKEND':'mongodb','MONGODB_URI':'mongodb+srv://cluster.example','ATLAS_STORAGE_DIR':'C:/private/path'},clear=True):
            config=Settings.from_env()
        self.assertEqual(config.storage_dir,Path('/tmp/solution-atlas'))
        self.assertEqual(config.llm_provider,'gemini')
