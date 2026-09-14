"""Run the single-user local application from the repository root."""
import sys
from pathlib import Path

# Optional offline dependency cache; normal installations use requirements.txt.
vendor = Path(__file__).resolve().parents[1] / '.runtime' / 'vendor'
if vendor.exists():
    sys.path.append(str(vendor))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('backend.app:app', host='127.0.0.1', port=8000, workers=1)
