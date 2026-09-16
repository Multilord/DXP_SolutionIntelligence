# Solution Atlas — AI-Powered Solution Intelligence

Help enterprise support consultants find and reuse the best applicable resolution, inspect its evidence, and capture new knowledge when no reliable precedent exists.

**Updated stack: Gemini API + MongoDB Atlas + Vercel. No Claude API. Authentication is excluded from this prototype.**

## Honest implementation status

The interface uses free, open-source Radix UI primitives, cmdk keyboard search, Motion transitions, Sonner notifications, Lucide icons and locally bundled Inter typography. Press **Ctrl+K** (or **Cmd+K**) to navigate pages, select incidents or open source evidence. The navy-and-teal workspace adapts to mobile screens and respects reduced-motion preferences.

Gemini now powers the main analysis flow, semantic embeddings and cited synthesis. This remains a prototype; live checks and limitations below distinguish implemented code from enterprise readiness.

| Capability | Status at this planning checkpoint |
|---|---|
| Incident workspace, evidence, library and timeline | Working prototype |
| System-version applicability and change-history checks | Working deterministic safeguards |
| Resolution capture, review, publication and outcomes | Working workflow |
| PDF, DOCX, Markdown, text, CSV and JSON uploads | Working extraction; no OCR |
| MongoDB persistence and Vercel configuration | Atlas connectivity restored after renewing the expired network rule. Deployed health, workspace, index and connectors endpoints passed; fresh Gemini + Atlas analysis passed on Vercel. |
| Gemini incident understanding and grounded synthesis | Implemented; structured output, server-owned source passages and a grounding verification pass |
| Semantic embeddings and hybrid retrieval | Implemented; versioned 768-dimensional Gemini embeddings and Atlas Vector Search |
| Outcome-informed ranking and AI evaluation | Implemented version/system-scoped outcomes, automated tests and live synthetic evaluation command |
| Source synchronization | SharePoint Graph delta and normalized SAP/KB/ticket feed adapters implemented; real source credentials/testing still required |

Setting LLM_PROVIDER=disabled enables a clearly labelled **limited non-AI demo**. Gemini mode fails explicitly on missing credentials, quota errors, incomplete indexing or invalid citations; it does not silently substitute lexical-only results. Earlier documents proposing PostgreSQL/pgvector, mandatory Ollama or Docker hosting are historical; this README supersedes those choices.

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

## Environment

Store secrets in ignored `.env` locally and server-side Vercel environment variables. Never commit keys or use frontend `VITE_` variables for secrets.

```dotenv
DATABASE_BACKEND=mongodb
MONGODB_URI=mongodb+srv://USERNAME:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=solution_atlas
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
VECTOR_BACKEND=atlas
MONGODB_VECTOR_INDEX=atlas_semantic
```

Models are configurable and must be available to your account. Gemini configuration is required for the full AI experience. Missing keys, quota errors and unfinished indexes must be explicit, not silently disguised as AI success. Incident descriptions and retrieved source content are sent to Gemini when enabled.

SAP/SharePoint credentials are separate. See [connector setup and feed schema](CONNECTORS.md). Adapters sync explicitly from Knowledge sources; this is not a background scheduler or native SAP Notes access. Seed data is synthetic, not actual SAP guidance.

## Run and test

For a live demo rehearsal, run `python -m backend.demo_check`. It sends only bundled synthetic fixtures to Gemini, reads their matching Atlas embeddings, and writes results to an isolated temporary local database. It does not alter shared incidents. Scenarios are spaced 60 seconds apart to reduce rate-limit failures; account quota still applies. Use `--cases knowledge_gap quick_reference` to select scenarios. The sanitized report is saved to `.runtime/demo-check.json`. This verifies the laptop-to-service path; deployed `/api/health` must also succeed before recording against Vercel.

Use Python 3.12 and Node.js 22. Copy `.env.example` to `.env`, then fill the database URI and Gemini key.

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

## Semantic index setup

```powershell
python -m backend.manage_ai check
python -m backend.manage_ai index
python -m backend.manage_ai atlas-index
```

Wait for the Atlas index to report queryable before analyzing. The Knowledge sources screen also builds embeddings in resumable batches of 16 sections. New content or a changed model/version requires indexing; unpublished drafts and deleted sources cannot enter normal retrieval. This implementation filters current eligible chunk IDs in the Atlas query; large enterprise corpora need a scalable index lifecycle instead of loading eligibility records per request.

The model classifies intent, retrieves evidence and synthesizes findings with exact passage citations. Approved actions retain their reviewed wording/order. Unknown or incompatible context cannot be made safe by generated text. A second model check verifies claim support, but is not a proof of correctness. Repeated analyses reuse cached answers only while knowledge, system context, outcomes and model configuration are unchanged.

## Verification status

- 40 automated tests cover workflow, AI orchestration, draft/version exclusion, forged citations, action constraints, safe database failures and source updates/deletions.
- Frontend production build passed.
- Live MongoDB Atlas, Gemini generation and Gemini embeddings checks passed. Atlas vector index is queryable.
- September 16 live synthetic rehearsal verified all four scenarios across two runs: diagnostic question, guided runbook, no-precedent escalation and handover quick reference. Cited Gemini findings used real Atlas Vector Search; incompatible/stale alternatives and context invalidation were also verified. Rapid consecutive scenarios hit Gemini rate limits; the remaining scenarios passed after spacing requests. This is not an enterprise accuracy benchmark or proof of Vercel connectivity.
- Live retrieval evaluation uses six synthetic unseen-wording cases in an isolated database: `python -m backend.manage_ai evaluate`. It spaces requests to reduce free-tier rate-limit failures. Results are not an enterprise accuracy benchmark.
- Real SAP/SharePoint synchronization is not verified without the organization's credentials and permitted source data.
- See [Vercel deployment](DEPLOY_VERCEL.md) for deployment requirements and limitations.

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
