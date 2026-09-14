# Solution Atlas — Complete Local Build Pipeline

For the consolidated product description and all updated flows in one place, start with [SOLUTION_BLUEPRINT.md](SOLUTION_BLUEPRINT.md). This file remains the detailed engineering companion.

The supplied Aegis proposals have been reviewed in [AEGIS_IDEAS_REVIEW.md](AEGIS_IDEAS_REVIEW.md). Section 17 adds scoped change history, knowledge-gap capture, evidence signals, and typed answers to the build. Local inference remains mandatory.

## 1. Architecture decision

Build a modular monolith: one backend organized into clear modules, with one background worker. The frontend, database, and model runtime are separate processes. This keeps the prototype understandable and economical on 16 GB RAM and the device-reported GTX 1650 with 4 GB VRAM.

The only generation provider is local Ollama running a quantized Qwen3-4B model. No Claude API, other hosted model API, cloud fallback, paid middleware, or managed database is part of the build. Packages and model weights are downloaded during setup; the completed application must run against its local corpus without internet access.

This document is an implementation specification, not a claim that the application has been built or benchmarked. It refines the earlier prototype blueprint and free-stack proposal. Software has no subscription charge; hardware, electricity, development effort, and proprietary source entitlements remain separate.

```text
                     LOCAL COMPUTER

 Browser: React + Vite build + Tailwind CSS
    | upload / open incident / answer question / record outcome
    | HTTP JSON and multipart uploads; poll job progress
    v
 FastAPI application
    | request middleware + identity/authorization dependencies
    | incident / source / knowledge / recommendation / outcome services
    | SQLAlchemy unit of work + Psycopg database driver
    |
    +---------------------------> PostgreSQL + pgvector
    |                              structured data, chunks, jobs, audit
    +---------------------------> Local source files

 Python worker <---------------- PostgreSQL job queue
    | extraction -> chunking -> MiniLM embeddings on CPU
    | authorized retrieval -> applicability rules -> prompt assembly
    v
 Ollama on localhost:11434
    | Qwen3-4B, quantized; one generation at a time
    v
 Worker validates output -> saves recommendation -> frontend reads result
```

The browser never connects directly to PostgreSQL, raw source storage, or Ollama. The database stores facts and history; the worker performs expensive operations; the API enforces access at every user-facing endpoint.

## 2. Technology and responsibility map

| Layer | Technology | Responsibility |
|---|---|---|
| Presentation | React, TypeScript, Vite, Tailwind CSS | Screens, forms, source previews, loading states, keyboard interactions |
| HTTP API | Python, FastAPI, Pydantic | Request validation, response contracts, service entry points |
| Data access | SQLAlchemy, Psycopg | Parameterized queries, transactions, database connections |
| Schema evolution | Alembic | Reviewed, versioned database migrations |
| Database | PostgreSQL and pgvector | Relational records, full-text search, embeddings, job queue |
| Embedding inference | Sentence Transformers, all-MiniLM-L6-v2 | Local English text embeddings on CPU |
| Text generation | Ollama, quantized Qwen3-4B | Evidence explanations and drafts |
| File extraction | pypdf, python-docx, Python CSV/JSON/text readers | Parse supported uploaded documents |
| Password verification | argon2-cffi | Hash and verify local account passwords |
| Background execution | Custom Python worker with PostgreSQL leases | Durable jobs, retries, progress, cancellation |
| Testing | pytest, Playwright | Rule, database, retrieval, and browser tests |

SQLAlchemy manages transactional work; Alembic maintains schema revisions, and Psycopg connects Python to PostgreSQL. These are libraries within the backend rather than additional servers. [SQLAlchemy sessions](https://docs.sqlalchemy.org/en/20/orm/session_basics.html), [Alembic](https://alembic.sqlalchemy.org/en/latest/), [Psycopg](https://www.psycopg.org/psycopg3/docs/), [argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/).

## 3. Frontend: what consultants interact with

### Screens

| Screen | Components | Main behavior |
|---|---|---|
| Login | Account form, session-expired state | Establish a local authenticated session |
| Incident workspace | Incident list, context editor, diagnostic question, recommendation panel | Analyze an incident and review its next action |
| Evidence drawer | Source section, version, context differences, supporting references | Inspect the exact evidence behind a recommendation |
| Source manager | File upload, source category, scope, ingestion progress, parser errors | Add permitted knowledge and see ingestion status |
| Solution library | Passport list, applicability, approved steps, outcome history | Browse reusable procedures |
| Knowledge review | Draft receipt, proposed changes, reviewer decision | Approve or reject knowledge changes |
| Recurrence view | Reviewed incident families and outcome counts | Identify repeated effort without inventing predictive metrics |
| Local health | API, database, worker, model status | Explain unavailable capabilities and degraded operation |

### Consultant workspace layout

Use context on the left, the next action in the center, and evidence on the right. The center has one primary recommendation and at most two alternatives. Context fields display provenance and whether they are confirmed or unknown.

The frontend never computes an authoritative applicability decision. It renders the backend's checks: match, mismatch, unknown, or needs review. Editing an environment fact increments the incident revision and visibly marks existing recommendations stale.

Use ordinary React state for form drafts and a small typed fetch wrapper for server requests. Generate or validate TypeScript contracts against FastAPI's OpenAPI schema to avoid mismatched field names. Keep authenticated content out of persistent browser storage in the first version.

### Progress and error behavior

Starting an analysis returns a job ID immediately. The frontend polls an authorized job endpoint, initially once per second and backing off when unchanged. Display real stages such as retrieving, checking applicability, queued for model, generating, validating, and complete; do not show fabricated completion percentages.

The interface can display validated source matches before generation finishes. Generated operational instructions appear only after backend validation. A malformed model response must never briefly appear as approved advice. Reloading the page can resume an existing job, and canceling a job prevents its result from being published.

Provide distinct states for no matching knowledge, insufficient prerequisites, contradictory evidence, unsupported file type, worker unavailable, model unavailable, and stale recommendation. A search with no supported fix should still offer authorized evidence and a structured escalation packet.

## 4. Backend: the application’s decision logic

Organize the backend into modules with explicit contracts:

| Module | Inputs | Outputs |
|---|---|---|
| Identity and scope | Session cookie, membership records | Trusted actor and permitted client scopes |
| Incident service | Ticket text and confirmed context | Versioned incident plus observations |
| Source service | Approved upload and source metadata | Document version and ingestion job |
| Extraction service | Stored file | Structured sections with location references |
| Retrieval service | Normalized incident and authorized scope | Ranked evidence sections and linked passports |
| Applicability engine | Environment facts and passport prerequisites | Explicit check results and eligible candidates |
| Diagnostic engine | Unresolved checks and authored branches | Next useful question or escalation |
| Generation adapter | Selected evidence and fixed response schema | Untrusted structured draft from local Ollama |
| Recommendation validator | Draft, selected evidence, policy decisions | Validated result or evidence-only fallback |
| Outcome service | Confirmed actions and validation result | Append-only outcome event and draft receipt |
| Knowledge review service | Proposed passport changes | New approved version or rejected draft |

Keep business rules outside route handlers. Routes validate and authorize; services coordinate; repositories read and write data. Both the API and worker use the same applicability and authorization implementations to prevent inconsistent behavior.

Use short database transactions. Load a versioned evidence/context snapshot, commit, call Ollama, then open a new transaction to recheck source permissions, active versions, and incident revision before saving the result. Do not keep database row locks open while waiting for inference.

## 5. Middleware: shared handling around application work

Middleware handles concerns that recur across requests. Authorization dependencies and service policies complement it; they are not all literally HTTP middleware. FastAPI documents request/response middleware and configurable CORS. [Middleware](https://fastapi.tiangolo.com/tutorial/middleware/), [CORS](https://fastapi.tiangolo.com/tutorial/cors/).

| Concern | Where it belongs | Behavior |
|---|---|---|
| Request ID and timing | HTTP middleware | Attach a traceable ID and record duration/status |
| Host/origin validation | Middleware and configuration | Accept configured local hosts; reject unexpected origins |
| CORS | Middleware only if separate origins are used | Allow specific development origins, not wildcard credential access |
| Authentication | FastAPI dependency | Validate the server-side session and resolve actor |
| Authorization | Dependency, service policy, database policy | Check client membership and object permissions |
| Request validation | Pydantic and upload handler | Validate types, length limits, source categories, file limits |
| CSRF defense | Dependency for state-changing requests | Check CSRF token and origin when using cookie sessions |
| Error translation | Exception handlers | Return consistent errors without stack traces or secrets |
| Admission limits | Service policy | Bound job queue depth and prevent duplicate analyses |
| Transactions | Repository/unit of work | Commit complete changes or roll them back |
| Job retries | Worker | Retry transient failures with bounded attempts and backoff |
| Output validation | Recommendation service | Check schema, references, and correspondence to approved steps |

For the desktop prototype, prefer one browser origin: Vite proxies `/api` during development; the backend serves the built UI for the demo. CORS is not authentication and is not a substitute for checking the user.

Use random opaque session tokens, store only token hashes in PostgreSQL, expire sessions, and rotate on login. Cookies are HttpOnly and SameSite; require Secure cookies and TLS before deployment beyond an explicitly localhost-only development configuration. Roles are consultant, knowledge reviewer, and administrator. Permissions must be based on server-side memberships, never a client-supplied role or tenant header.

This middleware is implemented in the existing backend. Redis, Kafka, RabbitMQ, a paid gateway, and a separate identity server are not prerequisites for this laptop build.

## 6. Database: persistent facts, evidence, and work

### Proposed logical tables

All customer-scoped tables include tenant/client scope, timestamps, and appropriate foreign keys. Use UUID identifiers. Use composite scope-aware foreign keys or equivalent constraints to prevent links between unrelated clients.

| Table group | Main fields / purpose |
|---|---|
| `users`, `sessions`, `memberships` | Password hash, session expiry, actor-to-client roles |
| `sources` | Category, owner, source location, access policy, active status |
| `documents` | Logical source identity and current version pointer |
| `document_versions` | Immutable content hash, source revision, storage key, available-at timestamp, parser version, ingestion status |
| `document_sections` | Version, heading, page/paragraph locator, extracted text |
| `chunks` | Section ID, chunk order, text, token count, full-text vector, embedding `vector(384)`, embedding model revision |
| `access_grants` | Policy-to-user/role grants within a client scope |
| `incidents` | Title, description, request type, environment snapshot, revision, current state |
| `observations` | Incident, field, value, provenance, actor, observed-at time |
| `passports`, `passport_versions` | Procedure identity, owner, immutable version, lifecycle state, applicability rules |
| `passport_steps`, `step_evidence` | Ordered approved actions, expected results, stop conditions, source-section links |
| `diagnostic_branches` | Questions, answer types, branch conditions, next action identifiers |
| `recommendation_runs` | Incident revision, model/configuration version, checks, result state, explanation |
| `recommendation_evidence` | Exact source sections and passport versions used by a run |
| `outcome_events` | Attempted/confirmed/failed/unknown/reopened events and verification evidence |
| `knowledge_drafts`, `review_events` | Proposed changes and accountable approval history |
| `jobs` | Type, priority, state, attempts, lease, heartbeat, progress, actor, scope, idempotency key |
| `audit_events` | Actor, action, object ID, timestamp, request/job ID, minimal metadata |

Use relational columns for identity, status, versioning, and joins. Use JSONB for variable environment facts and typed prerequisite definitions, validated by application schemas. Do not put the entire application into one JSON column.

Source files remain on disk; PostgreSQL holds their metadata, extracted text, and references. Store uploads under server-generated keys and serve them through authorized endpoints. Do not use supplied filenames as filesystem paths.

### Relationships

```text
Source -> Document -> DocumentVersion -> Section -> Chunk
                              ^             ^
                              |             |
Passport -> PassportVersion -> Step -> StepEvidence

Incident -> Observations
Incident -> RecommendationRun -> RecommendationEvidence
Incident -> OutcomeEvent -> PassportVersion
OutcomeEvent -> KnowledgeDraft -> ReviewEvent -> new PassportVersion

User -> Membership -> Client scope
Job -> requesting actor + client scope + target object + input revision
```

### Indexes and access rules

Start with B-tree indexes on scope, status, source identity, and foreign keys, plus a GIN index for the full-text column. For the small prototype corpus, use exact vector distance search over authorized chunks. Add an HNSW index only after profiling shows a need. Approximate vector search with restrictive filters can return too few results; pgvector documents filtering and iterative scan options. [pgvector](https://github.com/pgvector/pgvector).

Enable row-level security on scoped records as a second boundary alongside application authorization. Use an application database role that neither owns the tables nor has superuser/BYPASSRLS privileges; migrations use a separate role. Set validated scope transaction-locally so pooled connections cannot retain another request's identity. Review policy behavior for joins, derived results, and worker access. [PostgreSQL row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html).

User-visible recommendation runs inherit restrictions from all supporting sources. If a source becomes unavailable to the viewer, withhold the derived answer or regenerate from permitted evidence. Counts and source titles must follow the same rules. A session belonging to a client does not automatically grant access to every document in that client.

## 7. Pipeline A: knowledge ingestion

1. **Upload:** the frontend submits a file, declared source category, permitted scope, and metadata.
2. **Admission:** the API checks actor permissions, actual file type, size, and supported format. Start with a configurable 10 MB per-file limit; reject archives and password-protected/unsupported files.
3. **Store:** write a temporary file under a generated key, calculate its hash, and finalize its location. Create the version and job transactionally; reconcile orphan files if a database write fails.
4. **Deduplicate:** use source identity, scope, content hash, and extraction revision. Re-uploading identical content should not create duplicate indexed evidence; do not expose cross-client deduplication information.
5. **Extract:** the worker parses text PDF, DOCX, Markdown/text, CSV, or JSON into structured sections. Run parsing with bounded time and resource use. Scanned PDFs initially show “OCR required.”
6. **Normalize:** preserve error identifiers, headings, ordered steps, product versions, and source locators. Flag weak resolution notes rather than inventing missing actions.
7. **Chunk:** use the MiniLM tokenizer, targeting approximately 180–220 word pieces per chunk with modest overlap and heading overhead inside the model's 256-word-piece default limit.
8. **Embed:** run MiniLM on CPU in small batches. Store vectors and the exact embedding model revision.
9. **Index:** populate full-text and exact-identifier fields. Mark the new version searchable only after successful completion; do not expose partial ingestion.
10. **Review:** create a knowledge draft only when evidence is sufficient. Uploading a ticket does not automatically create an approved procedure.

MiniLM provides 384-dimensional embeddings and is a short English text baseline. Chunking must respect its input limit rather than blindly embedding full documents. [Model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).

On a source update, keep immutable history, switch the current searchable version after successful processing, and invalidate affected recommendations. On permission revocation or deletion, deny retrieval and previews immediately; purge derived artifacts according to the source retention policy. Backups require their own retention handling.

## 8. Pipeline B: incident analysis and recommendation

1. The consultant enters or opens an incident and confirms known context.
2. The API validates the incident revision, permissions, and idempotency key, then creates an analysis job.
3. The worker rechecks authorization and reads a consistent input snapshot.
4. Normalize narrative text while preserving error codes and distinguishing incidents from catalog-style requests.
5. Run exact-identifier, PostgreSQL full-text, and semantic retrieval against authorized, active evidence.
6. Merge rankings using reciprocal rank fusion and deduplicate shared sources. Start with up to 20 candidates from each retrieval channel; tune from evaluation.
7. Resolve linked passports and evaluate hard prerequisites. A mismatch excludes the operational procedure; unknown prerequisites trigger a question. Authorized mismatching evidence can still explain why a candidate was excluded.
8. Select an authored diagnostic question when its answer can change the next action. This path does not need an LLM call.
9. For supported candidates, assemble a compact prompt containing only the selected facts and relevant source excerpts. The model explains an approved action; it does not invent procedure steps.
10. Ask local Ollama for a JSON-schema-constrained draft with explanation and references. Structured output support does not establish factual correctness. [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs).
11. Validate the schema, reference IDs, evidence availability, allowed action IDs, and compatibility checks. Reject unknown steps or unresolved contradictions. Automated validation cannot prove every explanatory sentence; preserve source inspection and expert review.
12. Recheck incident revision and source access before saving. Mark a changed-input result stale rather than presenting it as current.
13. Return the validated recommendation or a useful evidence-only/escalation response.

Candidate retrieval ranks evidence relevance; it is not a probability of resolution. The UI displays prerequisite status and observed counts, not a fabricated confidence percentage.

## 9. Pipeline C: outcomes and knowledge improvement

The consultant records whether a proposed action was merely viewed, attempted, confirmed successful, unsuccessful, or still unverified. Save an idempotent outcome event with the exact passport version, incident context, and validation method.

Generate a short local draft receipt if the consultant requests it. Prefer proposing an update to an existing passport over creating a duplicate. A reviewer approves material procedure changes as a new version. A reopened incident adds a correcting event; historical evidence is not silently rewritten.

This is how the system learns initially: new evidence, reviewed procedures, and outcome records change what it can retrieve and recommend. No model fine-tuning or training job is needed on this laptop.

## 10. Durable jobs and inference scheduling

Use one worker process, holding MiniLM once in CPU memory. It handles ingestion and analysis jobs; only Ollama holds the generation model. API processes do not load a second embedding or generation model.

Claim a queued job using a short transaction with `FOR UPDATE SKIP LOCKED`, set a lease and worker token, then commit before performing work. Renew the lease with a heartbeat; only the current lease token may finalize a result. Expired jobs are recoverable, bounded retries handle transient errors, and permanent parse/schema errors become visible failures. PostgreSQL describes `SKIP LOCKED` as useful for queue-like consumers. [SELECT documentation](https://www.postgresql.org/docs/current/sql-select.html).

Give interactive analysis higher priority than ingestion. Ingestion checkpoints after small batches so new analysis can run; an active inference cannot be preempted instantly. Cancellation discards unpublished output and cooperatively stops the active operation. Admission limits keep the queue bounded.

Do not use FastAPI's in-process background tasks for durable ingestion. Process restarts must not lose submitted work. Unique job keys prevent double-clicks and retries from duplicating outcomes or rebuilding identical documents.

## 11. Local model configuration for this device

| Setting | Starting proposal |
|---|---|
| Model | Quantized Qwen3-4B; pin downloaded model digest and verify quantization |
| Context | 2,048 total tokens initially |
| Output allowance | Approximately 350–450 tokens per explanation |
| Prompt budget | Approximately 1,400–1,500 tokens including template/schema overhead; measure actual usage |
| Thinking | Disabled for the supported Qwen variant to keep the task focused |
| Parallel generations | One |
| Loaded generation models | One |
| Embeddings | CPU; small batches |
| Idle unloading | Short keep-alive, adjusted after warm/cold measurements |
| Failure path | Evidence and approved checklist remain available without generated prose |

A 2,048-token context includes both the prompt and output budget. Do not paste entire tickets and runbooks into it. Use an exact tokenizer or conservative budget with measured prompt counts, and reject/trim oversized prompts before inference. Increase to 4,096 only after observing RAM/VRAM headroom.

Ollama's chat API exposes format, thinking, runtime options, keep-alive, and timing/token counts. Use those measurements for warm latency, cold loading, and generation duration. Its FAQ documents context configuration and `ollama ps` for checking GPU versus CPU placement. [Chat API](https://docs.ollama.com/api/chat), [Ollama FAQ](https://docs.ollama.com/faq).

Use native Windows Ollama for the initial GPU path. PostgreSQL can be native if pgvector is installed successfully, or run in a small Podman Linux VM. Keep the API and worker native initially. If using a VM, start with a modest allocation and monitor total memory; a container is not a guarantee of negligible RAM usage. Avoid running optional identity servers and heavy dashboards during the demo.

The workspace is in a OneDrive-synced directory. Keep source code there if desired, but place live database volumes, uploaded enterprise data, model caches, session secrets, and runtime logs in a deliberately selected local runtime directory outside file synchronization. Do not store a running database's files in a sync folder. This is a proposed deployment location decision, not an action already performed.

## 12. HTTP contract

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/login`, `POST /api/auth/logout` | Establish/end session |
| `GET /api/me` | Return actor and permitted scopes |
| `POST /api/sources/{id}/uploads` | Queue a validated document upload |
| `GET /api/jobs/{id}` | Authorized status, stage, and result reference |
| `POST /api/jobs/{id}/cancel` | Cancel queued/active work cooperatively |
| `GET /api/incidents`, `POST /api/incidents` | List/create permitted incidents |
| `GET /api/incidents/{id}`, `PATCH /api/incidents/{id}` | Read/update context using expected revision |
| `POST /api/incidents/{id}/analyses` | Create asynchronous recommendation job |
| `POST /api/incidents/{id}/observations` | Record a diagnostic answer |
| `GET /api/recommendations/{id}` | Read validated result after current permission checks |
| `GET /api/evidence/{section_id}` | Open exact authorized source passage |
| `GET /api/passports/{id}` | Read applicable published knowledge |
| `POST /api/incidents/{id}/outcomes` | Save an idempotent result event |
| `GET /api/knowledge-drafts`, `POST /api/knowledge-drafts/{id}/review` | Review and promote knowledge |
| `GET /api/health` | Minimal local service readiness |

Job creation returns HTTP 202 with job ID and polling URL. Successful writes return the new revision. Use 409 for stale revisions, 413 for oversized uploads, 422 for invalid inputs, 429 for admission limits, and 503 for unavailable required services. Object lookup responses must not disclose whether another client owns an inaccessible identifier.

Example result shape, with synthetic identifiers:

```json
{
  "incident_id": "SYN-1042",
  "incident_revision": 3,
  "status": "diagnostic_needed",
  "checks": [
    {"field": "deployment", "result": "match"},
    {"field": "alternate_path_works", "result": "unknown"}
  ],
  "next_question": {
    "id": "SYN-Q-01",
    "text": "Does the same action work through the alternate application path?",
    "allowed_answers": ["yes", "no", "unknown"]
  },
  "evidence_section_ids": ["SYN-SECTION-12"],
  "generation_used": false
}
```

## 13. Proposed repository organization

```text
frontend/
  src/components/           reusable accessible controls
  src/features/incidents/   workspace and diagnostic UI
  src/features/evidence/    source previews
  src/features/knowledge/   passport and review screens
  src/features/sources/     uploads and ingestion states
  src/api/                  typed API client
backend/
  app/api/                  routes and request dependencies
  app/middleware/           request IDs, origin handling, logging
  app/schemas/              Pydantic input/output schemas
  app/services/             incident, source, outcome, review services
  app/retrieval/            lexical, vector, fusion, evidence selection
  app/rules/                applicability and diagnostic branches
  app/inference/            local Ollama adapter and output validation
  app/db/                   models, repositories, policies, sessions
  app/worker/               leases, dispatch, ingestion and analysis jobs
  migrations/               Alembic revisions
  tests/                    rules, API, database and retrieval tests
fixtures/                   explicitly synthetic documents and incidents
evaluation/                 labeled cases, replay runner, metric outputs
scripts/                    local setup, health, start, stop, backup checks
docs/                       architecture and operating instructions
```

Actual source implementation starts only after this specification. Keep runtime files and secrets out of version control and outside the synced project directory. Pin compatible stable versions in lockfiles; the Python version used for this project must support the selected ML dependencies rather than blindly inheriting the machine's newest Python installation.

## 14. Build order and exit criteria

| Stage | Build | Exit criterion |
|---|---|---|
| 1. Hardware baseline | Verify local Ollama, Qwen load, GPU placement, short prompt timing, and RAM headroom | One bounded local generation succeeds, or evidence-only mode is selected |
| 2. Project skeleton | React page, FastAPI health route, database connection, local start/stop scripts | Browser reaches API; services restart cleanly |
| 3. Schema and identity | Migrations, local accounts, sessions, scope memberships, core constraints/RLS | Two test users cannot access each other's restricted records |
| 4. Data ingestion | Uploads, file extraction, sections, jobs, CPU embeddings | Repeated upload is idempotent; failures visible; restart resumes work |
| 5. Retrieval | Full-text, exact identifiers, vector retrieval, rank fusion, evidence previews | Known fixture evidence is found by exact and paraphrased queries |
| 6. Domain logic | Passports, applicability checks, diagnostic branches | A context mismatch blocks an attractive but inapplicable fix |
| 7. Local generation | Small prompt, structured response, citation validation, timeout fallback | Unsupported references and steps are rejected; no remote calls |
| 8. Consultant experience | Complete workspace, progress, stale-state handling, evidence drawer | Primary and unknown-case workflows work with keyboard and mouse |
| 9. Learning workflow | Outcome events, draft receipts, knowledge review | Duplicate submissions do not inflate success; reviewer creates a new version |
| 10. Evaluation and packaging | Replay benchmark, failure cases, offline demo, backup/restore rehearsal | Local demo passes gates and limitations are recorded |

A focused prototype might take roughly 3–5 weeks for one experienced developer with access to a support specialist; this is a planning estimate, not a commitment. Build stages are ordered by dependencies, not by screen polish. Start with reviewed synthetic cases; larger real datasets follow after source access and data quality are understood.

## 15. Verification pipeline and acceptance

For each change, run the relevant Python tests, frontend type checks/build, database integration tests, and browser workflow tests. Use a disposable test database and synthetic data. A local script is sufficient; no paid CI service is required.

The release suite must include correct retrieval, prerequisite mismatch, unknown prerequisites, conflicting sources, source revocation, source deletion, invalid generated citations, prompt injection in a document, job crash/recovery, cancellation, stale context, duplicate outcome submission, and model unavailability.

Replay historical evaluation with only information available when the incident arrived. Keep eventual resolution and later documents out of the query context and index snapshot. Keep shared-outage duplicates together when splitting examples. Compare keyword-only retrieval, hybrid retrieval, and hybrid retrieval plus applicability rules before attributing improvement to generation.

Report answerability coverage, applicable top-three retrieval, unsupported-action rate, citation validity, and abstention quality with sample counts. Measure cold and warm end-to-end latency, peak RAM/VRAM, ingestion throughput, and queue wait separately. No response-time promise is justified until these measurements exist.

The final demonstration must run offline after setup, with no cloud credentials and no remote fallback. Show three outcomes: a supported procedure, a useful diagnostic question, and an honest escalation. Verify restoration from a database backup plus its matching source-file snapshot before considering the data durable.

## 16. Scope of the first build

Deliver local accounts, approved uploads, synthetic historical tickets, evidence retrieval, environment checks, diagnostic questions, locally generated explanations, reviewed receipts, and basic recurrence counts. Do not claim that uploads establish live SharePoint synchronization or SAP entitlement-aware retrieval.

Production remediation, autonomous SAP commands, foundation-model training, multilingual retrieval validation, continuous cloud connectors, OCR, and predictive outage prevention are later capabilities. The first build succeeds when it reliably connects an incident to an applicable, inspectable next action on the existing laptop.

## 17. Adopted Aegis improvements

### 17.1 Additional records

| Record | Required information |
|---|---|
| `system_instances` | Client, system identity, environment, component inventory, current snapshot revision, change-history coverage status |
| `system_change_events` | System, component/configuration scope, category, before/after state, effective-at and recorded-at times, applied/planned/reverted state, source provenance |
| `solution_validations` | Passport version, system/context snapshot, verification scope, observed-at/recorded-at times, outcome, validator, validation evidence |
| `change_solution_impacts` | Change and passport version, affected prerequisites, compatible/incompatible/unknown finding, reviewer, evidence |
| `temporal_assessments` | Recommendation run, assessment time, context/history revision, applicable validation IDs, relevant changes, freshness state, explanation codes |
| `gap_cases` | Incident/family, actor-visible scope, reason, owner, lifecycle state, linked resolution/draft, created/closed times |
| `support_routes` | Scope, component, approved escalation team/contact or queue, owner, active status |

All records inherit the existing scope and audit requirements. Two timestamps distinguish when an event occurred from when the system learned about it. Historical replay excludes information recorded after the replay cutoff, even if an event's effective date is earlier. Current queries use the latest known effective state. Preserve corrections as history.

### 17.2 Change-aware applicability algorithm

1. Resolve the incident's exact system/client scope and current component context.
2. Check hard passport prerequisites first. A known mismatch blocks the action without regard to similarity.
3. Find the latest successful validation whose procedure version and environment scope are applicable. A document's publication date or arbitrary ticket closure is not sufficient validation.
4. Inspect effective applied changes after that verification, through assessment time, scoped to the relevant system and prerequisites. Planned changes do not invalidate current state; reversions require state reconstruction rather than deleting history.
5. Use reviewed impact mappings where present. If impact or dependency scope is uncertain, require revalidation; do not assume either incompatibility or safety.
6. Return verified-current-context, relevant-change-needs-review, known-incompatible, context-history-incomplete, or no-relevant-change-recorded. The last label is an observation about available history, not proof of freshness.
7. Recheck the system/history revision immediately before publishing a recommendation. A newly recorded relevant event marks dependent runs stale and queues revalidation.

Do not subtract a fixed amount for every upgrade. If a heuristic freshness rank is added later, it can reorder otherwise eligible candidates but cannot override hard blocks or missing validation. No percentage is described as success probability without outcome-based calibration.

After a relevant change, the knowledge review queue shows affected passports. A reviewer can document continued applicability, revise the procedure, or retire it. Revalidation must include evidence and scope; a single click without verification cannot restore trusted status.

### 17.3 Evidence signals and answer contract

Extend the response with `answer_type`, `matched_signals`, `unmatched_signals`, `temporal_status`, `change_event_ids`, `validation_ids`, and `gap_case_id` when applicable. Each displayed signal identifies the observed field and supporting record; match chips are computed in code rather than supplied by Qwen.

| Answer type | Eligibility | Display |
|---|---|---|
| `quick_reference` | Supported low-risk informational answer | Short answer, citation, and any material condition |
| `guided_runbook` | Approved applicable procedure with required conditions satisfied | Ordered approved steps, validation, stop conditions, and routing when available |
| `diagnostic_question` | A missing observable condition can change the path | One typed question, reason, allowed answers |
| `escalation` | Insufficient usable evidence, unresolved conflict, or unsupported procedure | Confirmed context, attempted actions, evidence gaps, maintained support route if available |

Choose the allowed response type in application policy. Qwen may draft explanation but cannot change the type, lift a restriction, invent a contact, or assemble unreviewed procedural steps. Render operational steps from the approved passport version. Display source types with accessible text and color without implying a fixed authority hierarchy.

### 17.4 Knowledge-gap lifecycle

Create an explicit gap for `no_usable_precedent`, `context_missing`, `source_unavailable`, `ingestion_incomplete`, or `conflicting_evidence`. The user-visible explanation refers only to their accessible corpus. Ask for missing context or retry an unavailable source before labeling the case an undocumented problem.

Use open → assigned → resolution_captured → indexing → awaiting_review → published → closed, with rejected, indexing_failed, and reopened paths. Close a knowledge-coverage gap only after its approved version is searchable. Repeated queries may link to an existing gap after scoped normalization/review rather than creating duplicate work items.

The capture button saves confirmed actions and validation as an outcome plus draft. Existing metadata is prefilled, but the consultant confirms it. An ingestion job indexes the draft in an author/reviewer-only view; a reviewer then approves the version and normal recommendation visibility is activated transactionally. Index readiness and publication state are separate gates. Capture, indexing, and publishing remain idempotent.

If a reviewer edits a draft, reindex the exact approved revision before publication. An approval and index-readiness check must refer to the same immutable version; a previously indexed draft is not sufficient for changed text.

Track usability feedback separately from operational outcome events. Helpful/unhelpful ratings can nominate a source for review. Only comparable validated attempts contribute to outcome statistics, and a reopened case revises the derived summary without deleting original events.

### 17.5 API and build-order additions

Add authorized endpoints for system change history, recording validation evidence, listing gap cases, capturing a gap resolution, and reading reviewed support routes. Use the existing draft-review endpoint for promotion. Recording applied changes or publishing new procedures requires the appropriate administrative/reviewer role. No new server or paid dependency is introduced.

During schema stage 3, add systems, changes, validations, and gap tables. During domain-logic stage 6, add temporal assessment and typed-answer policy. During UI stage 8, add match chips, change warnings, response layouts, and the gap state. During stage 9, connect capture to indexing and approval. Implement revalidation invalidation before treating the freshness UI as complete.

### 17.6 Additional release tests

1. A relevant applied upgrade after validation changes the candidate to needing review.
2. An unrelated system/client/module change does not penalize the candidate or expose another client's change details.
3. An old document revalidated in the current context remains eligible.
4. Missing change history does not produce a verified-fresh label.
5. A known incompatible fix stays blocked despite a high relevance score or positive feedback.
6. Planned changes, reverted changes, and late-recorded events produce the intended current and historical assessments.
7. A source outage or incomplete indexing does not claim that the organization has no solution.
8. Captured drafts remain out of normal recommendations until indexing and review both succeed.
9. Approval produces a searchable version, and an equivalent later query finds it without model training.
10. Quick-reference format cannot bypass the policy for a production-changing procedure.
11. A missing support route yields an explicit missing-route state rather than a generated contact.
12. A cached answer becomes stale when the system history revision or applicable validation changes.
