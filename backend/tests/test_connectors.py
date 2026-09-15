import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from backend.core import Store, analyze
from backend.connectors import ConnectorError, ingest_records, sync, public_status, fetch


class ConnectorTests(unittest.TestCase):
    def setUp(self):
        self.store=Store(Path('.runtime/tests')/uuid.uuid4().hex)
        self.store.seed()
        self.record={'id':'KB-123','title':'Queue wait export','content':'QUEUE_WAIT jobs wait on a receiving service dependency. Inspect downstream availability.'}

    def test_source_upsert_is_idempotent_and_versioned(self):
        self.assertEqual(ingest_records(self.store,'kb','Internal KB',[self.record]),1)
        self.assertEqual(ingest_records(self.store,'kb','Internal KB',[self.record]),0)
        doc=next(d for d in self.store.all('documents') if d.get('source_id')=='KB-123')
        self.assertEqual(doc['version'],1)
        changed={**self.record,'content':self.record['content']+' The new release changes the dependency.'}
        ingest_records(self.store,'kb','Internal KB',[changed])
        self.assertEqual(self.store.get('documents',doc['id'])['version'],2)
        self.assertIsNone(self.store.get('documents',doc['id'])['passport_id'])

    def test_deletion_retracts_evidence(self):
        ingest_records(self.store,'kb','Internal KB',[self.record])
        before=analyze(self.store,'SYN-1043')
        ids={e['id'] for c in before['candidates'] for e in c['evidence']}
        doc=next(d for d in self.store.all('documents') if d.get('source_id')=='KB-123')
        self.assertIn(doc['id'],ids)
        ingest_records(self.store,'kb','Internal KB',[{'id':'KB-123','deleted':True}])
        after=analyze(self.store,'SYN-1043')
        self.assertNotIn(doc['id'],{e['id'] for c in after['candidates'] for e in c['evidence']})

    def test_feed_rejects_invalid_shape_and_never_exposes_token(self):
        with patch.dict('os.environ',{'SAP_FEED_URL':'https://source.example/export','SAP_FEED_TOKEN':'test-secret'},clear=True):
            with patch('backend.connectors.fetch',return_value=b'{"records": "wrong"}'):
                with self.assertRaises(ConnectorError):sync(self.store,'sap')
            self.assertNotIn('test-secret',str(public_status(self.store)))

    def test_no_configuration_does_not_claim_sync(self):
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaises(ConnectorError):sync(self.store,'sharepoint')

    def test_plaintext_urls_rejected(self):
        with self.assertRaises(ConnectorError):fetch('http://source.example/export')


if __name__=='__main__':unittest.main()
