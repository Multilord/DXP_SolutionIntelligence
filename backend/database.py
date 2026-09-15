"""Storage backends with a shared interface for the prototype domain layer."""
from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path

from .config import Settings
from .core import TABLES, Store


class Transaction:
    def __init__(self, session=None):self.session=session
    def execute(self, statement):
        if statement != 'BEGIN IMMEDIATE':raise ValueError('Unsupported transaction operation')


def session_args(transaction):
    return {'session':transaction.session} if transaction and transaction.session else {}


class MongoStore(Store):
    backend_name = 'MongoDB'

    def __init__(self, folder: Path, uri: str, database: str, client=None, require_transactions=False):
        self.folder = folder
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = None
        self._lock = threading.RLock()
        supplied_client = client is not None
        if not supplied_client:
            try:
                from pymongo import MongoClient
            except ImportError as error:
                raise RuntimeError('MongoDB mode requires pymongo. Install backend/requirements.txt.') from error
            client = MongoClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        self.client = client
        self.database_name = database
        self.db = client[database]
        if not supplied_client:
            self.client.admin.command('ping')
        self.transactions=require_transactions
        if require_transactions:
            topology=self.client.admin.command('hello')
            if not topology.get('setName') and topology.get('msg')!='isdbgrid':
                raise RuntimeError('Hosted MongoDB must support transactions (Atlas or a replica set).')
        for table in TABLES:
            self.db[table].create_index('id', unique=True)
        self.db.documents.create_index([('hash', 1), ('source_type', 1)])
        self.db.changes.create_index([('system_id', 1), ('component', 1), ('effective_at', -1)])
        self.db.validations.create_index([('passport_id', 1), ('system_id', 1), ('created_at', -1)])
        self.db.outcomes.create_index([('incident_id', 1), ('created_at', -1)])
        self.db.metadata.create_index('key', unique=True)

    @contextmanager
    def connect(self):
        if self.transactions:
            with self.client.start_session() as session:
                with session.start_transaction():
                    yield Transaction(session)
            return
        with self._lock:
            yield Transaction()

    def all(self, table, db=None):
        assert table in TABLES
        return [{k: v for k, v in row.items() if k != '_id'} for row in self.db[table].find({},**session_args(db)).sort('_id', 1)]

    def get(self, table, ident, db=None):
        assert table in TABLES
        row = self.db[table].find_one({'id': ident},**session_args(db))
        if not row:
            raise KeyError(ident)
        return {k: v for k, v in row.items() if k != '_id'}

    def put(self, table, data, db=None):
        assert table in TABLES
        clean = {k: v for k, v in data.items() if k != '_id'}
        self.db[table].replace_one({'id': clean['id']}, clean, upsert=True,**session_args(db))
        return clean

    def seed(self):
        from pymongo.errors import DuplicateKeyError, OperationFailure
        for attempt in range(3):
            try:
                with self.connect() as transaction:
                    args=session_args(transaction)
                    if self.db.metadata.find_one({'key':'seeded'},**args):return
                    self._seed(transaction)
                    self.db.metadata.insert_one({'key':'seeded','value':'1'},**args)
                return
            except (DuplicateKeyError,OperationFailure):
                if attempt==2:raise

    def ping(self):
        self.client.admin.command('ping')
        return True

    def vector_search(self, vector, index, eligible_ids):
        indexes=list(self.db.chunks.list_search_indexes(index))
        if not indexes or not indexes[0].get('queryable'):
            raise RuntimeError('Vector index is not queryable yet.')
        return list(self.db.chunks.aggregate([
            {'$vectorSearch':{'index':index,'path':'embedding','queryVector':vector,
                              'numCandidates':150,'limit':30,'filter':{'id':{'$in':eligible_ids}}}},
            {'$project':{'_id':0,'id':1,'document_id':1,'section_id':1,'vector_score':{'$meta':'vectorSearchScore'}}}
        ],maxTimeMS=8000))

    def ensure_vector_index(self, name):
        from pymongo.operations import SearchIndexModel
        existing=list(self.db.chunks.list_search_indexes(name))
        if not existing:
            self.db.chunks.create_search_index(SearchIndexModel(name=name,type='vectorSearch',definition={'fields':[
                {'type':'vector','path':'embedding','numDimensions':768,'similarity':'cosine'},
                {'type':'filter','path':'id'}]}))
            return {'name':name,'status':'building','queryable':False}
        row=existing[0]
        return {'name':name,'status':row.get('status','unknown'),'queryable':row.get('queryable',False)}


def create_store(config: Settings):
    if config.database_backend == 'mongodb':
        return MongoStore(config.storage_dir, config.mongodb_uri, config.mongodb_database, require_transactions=config.serverless)
    store = Store(config.storage_dir)
    store.backend_name = 'SQLite'
    store.database_name = str(store.path)
    return store


class LazyStore:
    """Build-time import must not require a live database connection."""
    def __init__(self,config):
        self.config=config
        self._store=None
        self._init_lock=threading.Lock()

    def __getattr__(self,name):
        if self._store is None:
            with self._init_lock:
                if self._store is None:
                    candidate=create_store(self.config)
                    if self.config.serverless:candidate.seed()
                    self._store=candidate
        return getattr(self._store,name)
