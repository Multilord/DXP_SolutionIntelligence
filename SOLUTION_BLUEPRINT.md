# Solution Atlas — Updated Solution and Build Blueprint

## 1. Solution overview

Solution Atlas is a local AI assistant for enterprise application support consultants. It finds relevant past resolutions, checks whether their procedures apply to the current system, explains supporting evidence, and captures verified outcomes as reusable knowledge.

The product promise is **Find what worked. Check what changed. Reuse what is still valid.**

It combines the original Solution Intelligence Engine design with the four useful Aegis proposals: change-aware validity, a visible evidence trail, a knowledge-gap capture loop, and answers formatted for the work required. These are product differentiators to evaluate, not claims that no competing product offers similar functionality.

This document is the consolidated target specification. A first local prototype is now implemented; see [README.md](README.md) for the actual feature coverage, startup instructions, verification and remaining work. It currently uses SQLite and keyword retrieval, with optional local Ollama explanations; it has not been performance-benchmarked. Authentication is excluded from this build at the user's request. The working project name remains Solution Atlas; Aegis refers to the supplied proposals.

### Confirmed constraints

- Local inference only: Ollama with quantized Qwen3-4B. No Claude API or other hosted inference.
- No required software subscription, paid model API, rented cloud service, or trial credit.
- Target device: 16 GB RAM and device-reported GTX 1650 with 4 GB VRAM.
- Initial sources: permitted local documents, ticket exports, and clearly labeled synthetic data.
- No automatic production changes. Consultants review procedures and record outcomes.
- All performance targets remain unverified until measured on the actual implementation.

Free software does not eliminate hardware, electricity, engineering effort, or existing SAP/SharePoint access costs. Offline use is required after initial dependency and model downloads.

## 2. Users and outcomes

| User | Main work | Desired outcome |
|---|---|---|
| Support consultant | Investigate a ticket and inspect recommended steps | Reach a supported next action with less repeated investigation |
| Knowledge reviewer | Review captured resolutions, conflicts, and stale procedures | Maintain reusable procedures with clear evidence and scope |
| Support lead | Inspect repeated incidents and unresolved knowledge gaps | Prioritize documentation and permanent remediation |
| Administrator | Maintain users, scopes, sources, and system changes | Keep the local application and access model dependable |

The engine supports restoration incidents and service requests. A service request with an approved catalog workflow should follow that workflow, including entitlements and approvals, rather than be treated as an unknown technical failure.

## 3. Core knowledge object: Solution Passport

A Solution Passport represents an approved reusable procedure. It is separate from the historical tickets that support it and the events recording its use.

| Passport content | Examples of stored information |
|---|---|
| Problem signature | Symptoms, exact error identifiers, component, business process |
| Applicability | Product, release, deployment, configuration prerequisites, exclusions |
| Diagnostic guidance | Questions, typed answers, branch conditions |
| Procedure | Approved ordered steps, expected observations, stop conditions |
| Evidence | Exact source sections and document versions |
| Validation | Checks that demonstrate technical and business recovery |
| Ownership | Maintainer, reviewer, lifecycle state, version |
| History | Comparable attempts, failed attempts, reopenings, revalidation |

A retrieved ticket can be useful context without containing an approved procedure. A successful outcome applies to the precise procedure version and environment observed. It is not proof that the same action works everywhere.

## 4. Four primary differentiators

### 4.1 Change-aware validity

Compare a procedure's relevant validation history with subsequent changes to the affected system and component. Store both when the change took effect and when it was recorded. Track planned, applied, reverted, and corrected events.

Do not discount every old ticket just because it is old. Unrelated upgrades should not change its applicability, and an old procedure revalidated in the current context can remain useful. A relevant change with unknown effect creates a review requirement; a verified incompatible prerequisite blocks the action.

Visible states are verified for current context, relevant change since verification, known incompatible, context/history incomplete, and no relevant change recorded. The last state describes available records; it does not guarantee freshness.

### 4.2 Evidence trail

Display observable match signals: exact error identifier, component, symptoms, environment, and relevant differences. Link each important step to its source passage and version. Use source-type labels and colors for navigation, not as a fixed reliability ranking.

Keep relevance, applicability, freshness, and observed outcomes distinct. Do not call a heuristic ranking score a probability that the fix will work. Explain uncertainty directly and show sample counts when reporting historical outcomes.

### 4.3 Knowledge-gap capture loop

Create an owned gap record when no usable precedent exists in the accessible corpus. Distinguish this from missing context, incomplete indexing, source unavailability, or conflicting evidence.

After manual resolution, the consultant confirms prefilled actions and validation. The system saves an outcome and draft, indexes it for the author/reviewers, and promotes it to ordinary recommendations only after approval. The gap closes when the approved answer is searchable.

### 4.4 Adaptive answer format

| Answer type | When used | Presentation |
|---|---|---|
| Quick reference | Supported low-risk informational question | Short answer with source and conditions |
| Guided runbook | Approved applicable procedure | Ordered steps, checks, stop conditions, approved routing |
| Diagnostic question | A missing observation could change the next action | One useful question and why it matters |
| Escalation | Unsupported, incompatible, or conflicting evidence | Known facts, attempted actions, gaps, maintained support route if available |

Application rules select the allowed format. Local Qwen drafts concise explanation within it. It cannot lift a restriction, invent an escalation contact, or combine unrelated ticket steps into an unreviewed procedure.

Supporting features include Failure Memory, the Resolution Receipt, and Recurrence Radar. Failed attempts are compared within relevant environments, receipts reduce documentation effort, and recurrence summaries help prioritize problem management. Forecasting future outages is outside the initial scope.

## 5. Technology stack and architecture

| Layer | Selected technology | Responsibility |
|---|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS | Consultant interface and review workflows |
| API | Python, FastAPI, Pydantic | Requests, validation, authorization, service coordination |
| Data access | SQLAlchemy and Psycopg | Queries, connections, transactions |
| Migrations | Alembic | Versioned database changes |
| Database/search | PostgreSQL, pgvector, built-in full-text search | Structured records, semantic/lexical retrieval, jobs |
| Embeddings | Sentence Transformers with all-MiniLM-L6-v2 | Local English short-text embeddings on CPU |
| Generation | Ollama with quantized Qwen3-4B | Evidence explanations and draft receipts |
| Extraction | pypdf, python-docx, Python text/CSV/JSON readers | Local file ingestion |
| Identity | Local accounts, opaque sessions, argon2-cffi | Authentication and role membership |
| Background processing | One Python worker using PostgreSQL jobs | Durable ingestion, analysis, and inference scheduling |
| Testing | pytest and local Playwright | Logic, database, API, and UI verification |

```text
                          LOCAL COMPUTER

                    React consultant interface
                               |
                     HTTP requests and job polling
                               v
                         FastAPI backend
                  validation / identity / permissions
                       application services
                         /             \
                        v               v
             PostgreSQL + pgvector    Local source files
                        ^               |
                        |               v
                     Python worker
              extract / embed / retrieve / assess
                        |
                        v
              Ollama: local Qwen3-4B
                        |
                        v
             validate / persist / present
```

Use a modular monolith, not a fleet of microservices. The browser never contacts PostgreSQL or Ollama directly. The worker loads MiniLM once; the API does not load another copy. Only Ollama holds the generation model. No Redis, Kafka, graph database, or hosted agent framework is required.

## 6. Frontend design

The main workspace has incident context on the left, the next action in the center, and an evidence drawer on the right. Known facts show their origin and observation time. Unknown facts remain explicit. Changing context increments its revision and marks older recommendations stale.

| Screen | Key interactions |
|---|---|
| Login | Establish/end local session |
| Incident workspace | Open incident, edit context, analyze, answer question, review plan |
| Evidence drawer | Inspect exact passage/version and matching or conflicting facts |
| Source manager | Upload permitted files, view indexing progress and failures |
| Solution library | Browse passports, prerequisites, validation and outcomes |
| System timeline | Inspect changes and affected procedures; authorized users record mock/verified events |
| Knowledge gaps | View reason, owner, status; capture verified resolution |
| Review queue | Review new knowledge and revalidate affected procedures |
| Recurrence/health | Inspect scoped summaries and local service readiness |

React displays server decisions rather than computing authoritative eligibility. A job returns immediately with an identifier; polling displays actual stages. Source matches can appear before generated explanation, but unvalidated operational advice must not flash onto the screen.

Keep the primary controls explicit: Analyze incident, View evidence, Answer question, Review resolution plan, Record outcome, Capture verified resolution, and Review knowledge. An Apply button is reserved for a visibly simulated demonstration, not production execution.

## 7. Backend and middleware

The backend contains incident, source, retrieval, applicability, temporal assessment, diagnostic, generation, outcome, gap, and review modules. Routes validate and authorize requests; services coordinate work; repositories access PostgreSQL. The API and worker share the same domain policies.

| Shared concern | Implementation location | Behavior |
|---|---|---|
| Request IDs and timing | HTTP middleware | Trace request/job and report duration |
| Host/origin controls | Middleware/configuration | Accept configured local origins |
| Authentication | FastAPI dependency | Resolve server-side session and actor |
| Authorization | Dependencies, service rules, database policy | Check object and client scope |
| Validation | Pydantic and upload handlers | Check types, revisions, sizes, supported formats |
| CSRF defense | State-changing route dependency | Validate token and origin for cookie sessions |
| Error handling | Exception handlers | Return consistent errors without secrets |
| Queue admission | Application service | Bound pending jobs and repeated submissions |
| Transactions | Repository/unit of work | Commit complete changes and roll back failures |
| Output checks | Recommendation validator | Verify schema, references, action IDs, and current eligibility |

Middleware is not a paid product in this architecture; these are shared controls within the backend. CORS is a browser-origin policy, not user authentication. Prefer one browser origin: Vite proxies API calls during development, and FastAPI serves the built static UI for the local demo.

Use short transactions. Read an authorized context/evidence snapshot, finish the transaction, call Ollama, then recheck incident revision, source access, and system history before saving. Do not hold database locks while generation runs.

## 8. Database model

| Domain | Tables |
|---|---|
| Identity | users, sessions, memberships, access_grants |
| Source knowledge | sources, documents, document_versions, document_sections, chunks |
| Support work | incidents, observations, recommendation_runs, recommendation_evidence |
| Procedures | passports, passport_versions, passport_steps, step_evidence, diagnostic_branches |
| System evolution | system_instances, system_change_events, change_solution_impacts |
| Verification | solution_validations, temporal_assessments, outcome_events |
| Learning | gap_cases, knowledge_drafts, review_events |
| Operations | support_routes, jobs, audit_events |

Documents have immutable versions; versions contain sections and chunks. Chunks carry searchable text, source references, and 384-dimensional embeddings. A passport version links ordered actions to source evidence. Recommendation runs record the exact context, procedure, and evidence versions used.

All client-scoped records carry tenant/client identifiers, constraints, and access policy. Source restrictions propagate to derived answers, previews, and counts. Revalidate access before displaying a previously generated answer. Database row-level security supplements application checks; the application role must not bypass it.

Use B-tree indexes for identifiers/scope and a GIN index for full-text retrieval. Begin with exact vector search over the authorized small corpus. Add approximate indexing only after testing its recall with permission filters.

File content lives under generated keys in an unsynced runtime directory. PostgreSQL stores metadata, text, vectors, and references. Do not place live database files, model caches, or confidential runtime data in the project's OneDrive-synced folder. This is a deployment requirement, not a directory change already performed.

## 9. Pipeline A — ingest knowledge

1. An authorized user uploads a permitted document or ticket export and specifies its source scope.
2. FastAPI validates size, actual format, access, and metadata. Start with bounded uploads; archives and unsupported encrypted files are rejected.
3. Store the file under a generated key and create an immutable version plus ingestion job. Handle filesystem/database partial failures explicitly.
4. The worker extracts text and section/page locations. Text PDFs, DOCX, Markdown/text, CSV, and JSON are in scope; scanned PDFs report that OCR is required.
5. Normalize structure while preserving technical identifiers, headings, conditions, and ordered procedures. Incomplete closure notes remain incomplete.
6. Split text into tokenizer-aware short chunks with overlap and parent links; do not exceed MiniLM's supported input budget.
7. Generate embeddings locally on CPU and store them with model revision and source provenance.
8. Populate lexical and exact-identifier search fields. Expose the new version only after indexing completes successfully.
9. Draft candidate knowledge for review when appropriate. Indexing a source does not automatically approve every instruction it contains.
10. On updates, deletions, or permission changes, invalidate affected results and enforce the new visibility immediately.

Local SharePoint-style uploads demonstrate document ingestion, not live synchronization. Restricted SAP Notes and enterprise repositories require existing authorization; they are not required for the synthetic offline prototype.

## 10. Pipeline B — analyze an incident

1. The consultant opens a ticket and confirms its system, component, release, symptoms, and known observations.
2. FastAPI validates actor, scope, revision, and idempotency key and queues analysis.
3. The worker rechecks permissions and reads the current snapshot.
4. Search exact identifiers, PostgreSQL full-text, and local semantic embeddings against active authorized evidence.
5. Combine rankings with reciprocal rank fusion, deduplicate shared incidents/documents, and resolve linked passports.
6. Apply hard prerequisites. Known incompatibility blocks a procedure regardless of textual relevance.
7. Check scoped system changes and validation history. Relevant uncertain changes require revalidation; absent history remains an uncertainty.
8. Select the response form. Ask a diagnostic question when a missing observation can change the path. Open a gap or escalation when useful evidence is unavailable.
9. For eligible answers, pack only the selected facts, approved action references, and short source passages into a bounded prompt.
10. Ask local Qwen for a structured explanation. It may summarize evidence but cannot authoritatively change applicability or procedural order.
11. Validate the response schema, references, and correspondence to approved actions. Discard invalid generation and retain useful evidence/checklists.
12. Recheck context, policy, and history revisions, save the result, and return it to the consultant.

Operational steps are rendered from the reviewed passport version. Multiple sources may corroborate a procedure; the model must not splice unrelated remedies into an unreviewed runbook. An escalation route comes from maintained data or is explicitly unavailable.

## 11. Pipeline C — react to a system change

1. An authorized user records a change or imports an approved change record, scoped to its system and affected areas.
2. Preserve effective time, recorded time, status, before/after conditions, and provenance.
3. Identify potentially affected passports using prerequisite relationships. Uncertain dependency coverage routes to review rather than being treated as irrelevant.
4. Mark dependent recommendations stale and create revalidation work.
5. A reviewer inspects the effect: still applicable, procedure needs revision, or incompatible.
6. Store validation evidence and scope. Publish a revised version or restore eligibility only where verified.

Planned changes do not alter the current effective state. Reversions reconstruct state rather than delete history. A late-recorded event affects present knowledge but is excluded from evaluations replayed before it was known.

## 12. Pipeline D — close a knowledge gap

```text
Open gap → Assign owner → Capture verified resolution
   → Index draft → Review → Publish → Confirm searchable → Close gap
```

Support missing-context, unavailable-source, incomplete-indexing, conflict, and no-usable-precedent reasons. Do not describe every weak result as missing organizational knowledge.

Prefill the receipt from incident facts and observations. The consultant confirms actual steps, outcome, and validation. Store an outcome event plus draft. The author and authorized reviewers can inspect the indexed draft; ordinary recommendations exclude it until approval.

If review edits the content, reindex the exact approved revision before publishing it. Approval of one revision must not publish different text. Failures and rejections remain visible, and an already published gap can reopen when later evidence invalidates its solution.

Keep viewed, helpful, attempted, confirmed, failed, unknown, and reopened events separate. A helpfulness vote is not a successful resolution. Duplicate submissions must not inflate outcome counts. Knowledge improves through reviewed records and retrieval updates, not model retraining.

## 13. API contract

| API group | Representative operations |
|---|---|
| Session | Login, logout, current user/scopes |
| Sources | Upload document, inspect version, retire source |
| Incidents | Create/open/update with expected revision, add observation |
| Analysis | Queue analysis, get recommendation, inspect evidence |
| Jobs | Read real progress, cancel, report failure |
| Systems | Read timeline, record scoped change, record validation |
| Knowledge | Read passport, review draft, publish indexed approved version |
| Gaps | List/assign gap, capture resolution, inspect closure state |
| Outcomes | Record idempotent attempt/result/reopening |
| Operations | Read scoped support routes, minimal health checks |

Long work returns HTTP 202 and a job ID. Use explicit stale-revision, validation, oversized-upload, admission-limit, and unavailable-service errors. Every object endpoint checks access. The browser cannot supply authoritative tenant membership or role.

Responses include answer type, matched/unmatched signals, applicability checks, temporal status, evidence references, incident revision, and optional gap ID. Model output never supplies permissions.

## 14. Worker and hardware plan

Use one Python worker and one concurrent generation. The worker claims jobs with a short PostgreSQL transaction, then releases locks before work. Leases, heartbeats, current-worker tokens, bounded retries, and idempotency permit recovery after a crash.

Give interactive analysis priority. Ingestion checkpoints after small batches so it can yield to new work. Canceling an active operation must prevent publication even if the underlying computation finishes. Bound the queue instead of allowing unlimited simultaneous requests.

| Setting | Starting proposal |
|---|---|
| Local model | Qwen3-4B, verified quantized artifact and pinned digest |
| Context | 2,048 total tokens initially |
| Prompt | Approximately 1,400–1,500 tokens, including formatting overhead |
| Output | Approximately 350–450 tokens |
| Embeddings | MiniLM on CPU, small batches, one loaded instance |
| Generation concurrency | One |
| Deployment | Native API/worker/Ollama; PostgreSQL native or in a small Podman VM |
| Model failure | Evidence, approved checklist, diagnostic question, or escalation remains usable |

These are starting settings, not guaranteed performance. Measure actual prompt tokens, warm/cold latency, CPU/GPU placement, RAM, and VRAM. Increase context only if headroom permits. Native Ollama uses the host GPU; a VM adds overhead and requires deliberate memory allocation.

Download dependencies and models during setup, then test with networking disabled. Do not configure external inference keys or a silent hosted fallback. Keep runtime ports local for the prototype.

## 15. Build sequence

| Stage | Deliverable | Completion gate |
|---|---|---|
| 1 | Hardware/model baseline | Bounded generation succeeds, memory and timing recorded |
| 2 | Frontend/API/database skeleton | Browser can read an authorized seeded incident |
| 3 | Schema, identity, migrations | Scope isolation and version constraints pass |
| 4 | Ingestion and durable worker | Repeated uploads are idempotent; interrupted work recovers |
| 5 | Hybrid retrieval and source previews | Exact and paraphrased queries find expected evidence |
| 6 | Passports, temporal checks, response routing | Mismatches and relevant changes produce correct restrictions |
| 7 | Local generation and validator | Invalid references/actions are rejected; no remote calls |
| 8 | Complete consultant interface | Answer, investigation, stale-state, and escalation flows work |
| 9 | Gap capture and knowledge review | Approved indexed capture is retrieved by a later query |
| 10 | Evaluation and demo packaging | Offline operation, failure cases, and backup restoration pass |

A 3–5-week focused prototype is a planning estimate for an experienced developer with domain-review support. Scope, data access, and hardware results determine the actual schedule. Build a working retrieval slice before adding all visible features.

## 16. Demonstration and evaluation

Prepare a small labeled synthetic corpus containing known fixes, differing environments, prior failures, relevant/unrelated changes, contradictory documents, and one genuine gap in the demo corpus. All synthetic system labels, counts, and actions stay marked as fictional.

The main demo opens an incident, shows match evidence, identifies a relevant change since verification, and asks a useful question. It then presents an appropriate supported path or a revalidation requirement. A second scene captures a manually resolved gap, waits for indexing, approves the record, and retrieves it through a paraphrased query.

Test correct retrieval, unknown prerequisites, incompatible fixes, unrelated changes, revalidation, revoked access, deleted sources, malformed model output, missing support routes, source outages, canceled jobs, and duplicate outcomes. Also test review edits requiring reindexing before publication.

For historical evaluation, freeze knowledge at incident arrival. Exclude future resolution notes, later documents, and changes not yet recorded. Group duplicate incidents from one outage when splitting examples. Compare keyword-only, hybrid search, and hybrid search with applicability to identify where the improvement comes from.

Report applicable top-three retrieval, citation validity, unsupported-action rate, appropriate escalation, gap closure, and actual timing with sample counts. Separate active consultant effort from elapsed ticket resolution time. Do not present synthetic 94% confidence or a sub-two-second target as measured results.

## 17. Scope and supporting documents

The first implementation delivers local uploads, synthetic ticket history, evidence retrieval, scoped temporal validity, diagnostic routing, local explanations, outcome recording, gap capture, and reviewed knowledge publication. Live enterprise connectors, OCR, multilingual retrieval validation, autonomous remediation, and outage prediction are later work.

The architecture is intended to produce an applicable and inspectable next action, including an honest request for more evidence when necessary. Human review remains necessary for operational correctness; schema and policy validation cannot prove every generated sentence is true.

Supporting specifications:

- [Detailed build pipeline](BUILD_PIPELINE.md): API examples, logical schema, middleware details, and acceptance tests.
- [Prototype blueprint](PROTOTYPE_BLUEPRINT.md): screen behavior, synthetic scenarios, and demonstration sequence.
- [Aegis ideas review](AEGIS_IDEAS_REVIEW.md): adopted ideas and corrections to the supplied proposals.
- [Free stack proposal](FREE_TECH_STACK.md): component licensing sources and cost boundaries.
- [Research report](SOLUTION_INTELLIGENCE_RESEARCH.md): supporting research and competitive context; this local-only blueprint supersedes its managed-service suggestions.
