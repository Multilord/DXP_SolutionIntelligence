# Deploy Solution Atlas on Vercel

The project is linked to multilords-projects/dxp-solution-intelligence. The preview build succeeds. Its Atlas connection currently fails during TLS negotiation although the laptop connection works; Atlas network access is being checked. Production is not declared ready. No Docker service is needed.

## Server environment

Configure Preview and Production:

| Variable | Value |
|---|---|
| DATABASE_BACKEND | mongodb |
| MONGODB_URI | Atlas URI with database-user credentials |
| MONGODB_DATABASE | Dedicated prototype database |
| LLM_PROVIDER | gemini |
| GEMINI_API_KEY | Your Gemini API key |
| GEMINI_MODEL | gemini-2.5-flash or another verified structured-output model |
| GEMINI_EMBEDDING_MODEL | gemini-embedding-001 |
| VECTOR_BACKEND | atlas |
| MONGODB_VECTOR_INDEX | atlas_semantic |
| ATLAS_ALLOWED_HOSTS | Optional custom domains |

Secrets stay server-side. Local .env files are excluded from deployment. The database must be reachable from Vercel and support transactions (Atlas or a replica set). No localhost database/model service will work remotely.

## Setup and deployment

```powershell
python -m backend.manage_ai check
python -m backend.manage_ai index
python -m backend.manage_ai atlas-index
python -m unittest discover -s backend/tests -v
npm run build
vercel deploy --yes
```

Embedding sends the configured source content to Gemini. Use synthetic or explicitly permitted prototype data. Wait until the Atlas vector index is queryable. Inspect the preview, then deploy production with `vercel deploy --prod --yes`.

## Hosting behavior

- FastAPI serves the compiled React frontend and API from the same origin.
- Vercel functions have a 60-second configured limit. Gemini calls share a 48-second budget, with bounded response sizes; rate-limit and provider errors are explicit.
- Semantic indexing runs in resumable batches of 16 sections, outside MongoDB transactions. Larger corpora require repeated index requests.
- Uploaded files are capped at 4 MiB. Extracted text persists in MongoDB; original uploaded bytes are not retained in hosted mode.
- Capture/publication use MongoDB transactions. Embeddings are built separately; missing embeddings block AI analysis until indexed.
- No permanent worker or persistent filesystem is required on Vercel. Local extraction uses a recoverable worker.
- Source sync is explicit and bounded; no scheduler or enterprise permission synchronization is implemented.
- Identical analyses can reuse a cached answer while incident, evidence, procedure versions, system history, outcomes and model configuration are unchanged.
- No authentication is implemented, as requested. Keep Vercel deployment protection and use a synthetic-data workspace; anyone with application access can modify its demo records.

## Verify the deployment

Check `/api/health`, `/api/configuration`, `/api/index` and the browser workspace. Analyze SYN-1043 and inspect Gemini citations, then test SYN-1042 diagnosis and SYN-1044 capture/review. Real organizational source connectors require additional service credentials and testing documented in CONNECTORS.md.

References: [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi), [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python).

Database initialization is deferred until an API request, so an unavailable database produces a safe 503 response instead of crashing the frontend at startup.
