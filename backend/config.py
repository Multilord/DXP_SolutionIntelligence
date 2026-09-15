"""Environment configuration. Secret values never enter API responses."""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
if not os.getenv('VERCEL'):
    load_dotenv(ROOT / '.env', override=False)


class ConfigError(RuntimeError):
    pass


def _value(name: str, default: str = '') -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    database_backend: str
    mongodb_uri: str
    mongodb_database: str
    storage_dir: Path
    llm_provider: str
    ollama_base_url: str
    ollama_model: str
    openai_api_key: str
    openai_model: str
    sap_base_url: str
    sap_client_id: str
    sap_client_secret: str
    sharepoint_tenant_id: str
    sharepoint_client_id: str
    sharepoint_client_secret: str
    serverless: bool = False
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-2.5-flash'
    gemini_embedding_model: str = 'gemini-embedding-001'
    vector_backend: str = 'local'
    vector_index: str = 'atlas_semantic'

    def allowed_hosts(self):
        hosts=['localhost','127.0.0.1','testserver']
        hosts += [h.strip() for h in _value('ATLAS_ALLOWED_HOSTS').split(',') if h.strip()]
        hosts += [_value(k) for k in ('VERCEL_URL','VERCEL_PROJECT_PRODUCTION_URL','VERCEL_BRANCH_URL') if _value(k)]
        return list(dict.fromkeys(hosts))

    @classmethod
    def from_env(cls) -> 'Settings':
        backend = _value('DATABASE_BACKEND', 'sqlite').lower()
        serverless = _value('VERCEL') == '1'
        provider = _value('LLM_PROVIDER', 'gemini').lower()
        if backend not in {'sqlite', 'mongodb'}:
            raise ConfigError('DATABASE_BACKEND must be sqlite or mongodb.')
        if provider not in {'gemini', 'ollama', 'openai', 'disabled'}:
            raise ConfigError('LLM_PROVIDER must be gemini, ollama, openai, or disabled.')
        vector_backend = _value('VECTOR_BACKEND', 'atlas' if serverless else 'local')
        if vector_backend not in ('atlas', 'local'):
            raise ConfigError('VECTOR_BACKEND must be atlas or local.')
        if vector_backend == 'atlas' and backend != 'mongodb':
            raise ConfigError('Atlas vector search requires MongoDB.')
        uri = _value('MONGODB_URI')
        if backend == 'mongodb' and not uri:
            raise ConfigError('MONGODB_URI is required when DATABASE_BACKEND=mongodb.')
        if serverless and backend != 'mongodb':
            raise ConfigError('Vercel deployment requires DATABASE_BACKEND=mongodb and a MongoDB Atlas URI.')
        if serverless and any(h in uri.lower() for h in ('localhost','127.0.0.1','[::1]')):
            raise ConfigError('Vercel requires a remotely reachable MongoDB URI.')
        if serverless and provider == 'ollama':
            raise ConfigError('Use LLM_PROVIDER=gemini on Vercel; local Ollama is not reachable.')
        key = _value('OPENAI_API_KEY')
        if provider == 'openai' and not key:
            raise ConfigError('OPENAI_API_KEY is required when LLM_PROVIDER=openai.')
        default_storage = Path(tempfile.gettempdir()) / 'solution-atlas' / 'local-prototype'
        return cls(
            database_backend=backend,
            mongodb_uri=uri,
            mongodb_database=_value('MONGODB_DATABASE', 'solution_atlas'),
            storage_dir=Path('/tmp/solution-atlas') if serverless else Path(_value('ATLAS_STORAGE_DIR', _value('ATLAS_DATA_DIR', str(default_storage)))).expanduser(),
            llm_provider=provider,
            ollama_base_url=_value('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/'),
            ollama_model=_value('OLLAMA_MODEL', 'qwen3:4b'),
            openai_api_key=key,
            openai_model=_value('OPENAI_MODEL', 'gpt-4.1-mini'),
            sap_base_url=_value('SAP_BASE_URL'),
            sap_client_id=_value('SAP_CLIENT_ID'),
            sap_client_secret=_value('SAP_CLIENT_SECRET'),
            sharepoint_tenant_id=_value('SHAREPOINT_TENANT_ID'),
            sharepoint_client_id=_value('SHAREPOINT_CLIENT_ID'),
            sharepoint_client_secret=_value('SHAREPOINT_CLIENT_SECRET'),
            serverless=serverless,
            gemini_api_key=_value('GEMINI_API_KEY'),
            gemini_model=_value('GEMINI_MODEL', 'gemini-2.5-flash'),
            gemini_embedding_model=_value('GEMINI_EMBEDDING_MODEL', 'gemini-embedding-001'),
            vector_backend=vector_backend,
            vector_index=_value('MONGODB_VECTOR_INDEX', 'atlas_semantic'),
        )

    def public_status(self) -> dict:
        return {
            'database': self.database_backend,
            'llm_provider': self.llm_provider,
            'llm_configured': bool(self.gemini_api_key) if self.llm_provider=='gemini' else self.llm_provider == 'ollama' or (self.llm_provider=='openai' and bool(self.openai_api_key)),
            'ai_mode': 'gemini' if self.llm_provider=='gemini' else 'limited_demo',
            'vector_backend': self.vector_backend,
            'sap_configured': bool(self.sap_base_url and self.sap_client_id and self.sap_client_secret),
            'sharepoint_configured': bool(self.sharepoint_tenant_id and self.sharepoint_client_id and self.sharepoint_client_secret),
            'runtime': 'vercel' if self.serverless else 'local',
        }


settings = Settings.from_env()
