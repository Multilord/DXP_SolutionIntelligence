# Solution Atlas — AI-Powered Solution Intelligence

Help enterprise support consultants find and reuse the best applicable resolution, inspect its evidence, and capture new knowledge when no reliable precedent exists.

**Updated stack: Gemini API + MongoDB Atlas + Vercel. No Claude API. Authentication is excluded from this prototype.**

## Honest implementation status

This README establishes the updated build contract before Gemini implementation. The repository is a prototype, not a completed enterprise integration. Previously prepared MongoDB/Vercel infrastructure changes will be published with the implementation.

| Capability | Status at this planning checkpoint |
|---|---|
| Incident workspace, evidence, library and timeline | Working prototype |
| System-version applicability and change-history checks | Working deterministic safeguards |
| Resolution capture, review, publication and outcomes | Working workflow |
| PDF, DOCX, Markdown, text, CSV and JSON uploads | Working extraction; no OCR |
| MongoDB persistence and Vercel configuration | Prepared locally; live deployment unverified |
| Gemini incident understanding and grounded synthesis | Next implementation |
| Semantic embeddings and hybrid retrieval | Next implementation |
| Outcome-informed ranking and AI evaluation | Next implementation |
| SAP and SharePoint live synchronization | Requires connector implementation and real source access; exports supported |

The existing lexical search is a **limited demo fallback**, not the finished AI engine. Optional AI explanations do not satisfy the main AI requirement. Earlier documents proposing PostgreSQL/pgvector, mandatory Ollama or Docker hosting are historical; this README supersedes those choices.

## Four differentiators

1. **Temporal applicability:** check module, deployment, release, verification and subsequent system changes. Reduce reliance on uncertain evidence and block known incompatibilities. Age alone does not prove a fix is wrong.
2. **Confidence and evidence:** show source type, document/version, passage citations and ranking signals. Evidence strength is not a calibrated probability of success.
3. **Knowledge gap capture:** record the human-verified resolution, review the exact version, index it for reuse and incorporate observed outcomes.
4. **Answer-type synthesis:** Gemini understands intent and produces a grounded reference, runbook, clarification or escalation. AI cannot override incompatibility or silently approve a procedure.

## Updated pipeline

1. Ingest authorized KB, historical ticket, SAP and SharePoint exports; preserve provenance and versions.
2. Extract text into bounded, inspectable sections and generate Gemini document embeddings.
3. Store knowledge, embeddings, procedures, system history and outcomes in MongoDB Atlas.
4. Use Gemini to understand incident symptoms, intent and missing context.
5. Retrieve with semantic similarity plus lexical and exact error-identifier matching.
6. Rank by relevance, system applicability, verification freshness and recorded outcomes.
7. Synthesize a cited answer; constrain executable actions to applicable reviewed procedures.
8. Capture, review and index new resolutions; use outcomes in future ranking.

“Learning” means updating searchable knowledge and outcome evidence, not retraining Gemini on every ticket. “Prediction” means ranking likely relevant resolutions, not forecasting incidents or claiming measured time savings.

## Architecture

| Layer | Technology and responsibility |
|---|---|
| Frontend | React, TypeScript, Vite, Lucide and responsive CSS; six consultant workflow screens |
| Backend | FastAPI/Pydantic; ingestion, AI orchestration, retrieval and applicability |
| AI | Gemini generation and embedding APIs; configurable model IDs and structured responses |
| Database | MongoDB Atlas for documents, vectors, incidents, procedures, changes, outcomes and jobs |
| Retrieval | Hybrid search; Atlas Vector Search target and explicitly labelled local test alternative |
| Middleware | Input validation, host/origin checks, safe errors, revision checks and transactional publication |
| Hosting | Vercel with remote MongoDB Atlas; no Docker required |

The 16 GB RAM / GTX 1650 Ti laptop is suitable for development because models run remotely. Gemini, Atlas and Vercel may provide limited free usage; unlimited free operation is not guaranteed.

## Environment — updated implementation target

Store secrets in ignored `.env` locally and server-side Vercel environment variables. Never commit keys or use frontend `VITE_` variables for secrets.

```dotenv
DATABASE_BACKEND=mongodb
MONGODB_URI=mongodb+srv://USERNAME:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=solution_atlas
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

Models are configurable and must be available to your account. Gemini configuration is required for the full AI experience. Missing keys, quota errors and unfinished indexes must be explicit, not silently disguised as AI success. Incident descriptions and retrieved source content are sent to Gemini when enabled.

SAP/SharePoint credentials are separate. Filling credential fields does not create a connector. Until configured and tested, source exports and synthetic fixtures are used; the seed data is not actual SAP guidance.

## Run and test

Use Python 3.12 and Node.js 22. The Gemini settings above become runnable with the implementation commit; the pre-integration code supports only its existing providers.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm ci
npm run build
.venv\Scripts\python.exe -m backend.run
```

Open http://127.0.0.1:8000; API explorer: http://127.0.0.1:8000/docs. Run `npm run dev` alongside the backend for frontend development.

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m unittest discover -s backend/tests -v
npm run build
```

## Acceptance checks

- Retrieve correct precedents from unseen paraphrases without exact error codes.
- Restrict stale and incompatible fixes even when semantically similar.
- Validate passage citations and reject unsupported executable steps.
- Exclude unpublished drafts; retrieve newly reviewed resolutions semantically.
- Incorporate outcomes without claiming small samples are reliable success probabilities.
- Expose AI configuration failures and incomplete semantic indexing clearly.
- Verify Atlas connectivity, vector-index readiness and deployed requests separately from mocked tests.

Authentication, permission synchronization, OCR and execution of changes in SAP are excluded. This is a shared demonstration workspace, not an enterprise production deployment. Live connectors and real model evaluation must be reported honestly until verified.

## References

- [Gemini embeddings](https://ai.google.dev/gemini-api/docs/embeddings)
- [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- [MongoDB Vector Search](https://www.mongodb.com/docs/vector-search/)
