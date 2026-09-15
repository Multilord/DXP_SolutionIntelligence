"""Check the selected backend and provider without printing secrets."""
from __future__ import annotations

import json

from .config import settings
from .database import create_store


def main():
    status = settings.public_status()
    store = create_store(settings)
    store.ping()
    print(json.dumps({
        'status': 'ok',
        'database': store.backend_name,
        'database_name': store.database_name,
        'storage_dir': str(settings.storage_dir),
        'providers': status,
        'secrets_exposed': False,
    }, indent=2))


if __name__ == '__main__':
    main()
