# Solution Atlas — Free Local Technology Stack

## Decision

Confirmed build constraint: no Claude API or other hosted inference. [BUILD_PIPELINE.md](BUILD_PIPELINE.md) defines the implementation using local Qwen3-4B, one worker, and the device's 16 GB RAM / 4 GB VRAM budget. Qwen3-8B below remains an optional future hardware-dependent evaluation, not the selected model.

Use React, Vite, Tailwind CSS, FastAPI, PostgreSQL with pgvector, Sentence Transformers, and local Ollama inference with Qwen3. Deploy on an existing computer using native processes or Podman. All required application components have no software subscription or per-request API charge in this deployment.

This replaces the paid managed-service candidates in the original research report for the current project. It is a proposal, not an installed or tested system. License information was checked against primary project pages and model cards on September 15, 2026; pin exact dependency versions and retain their license notices when implementing.

“Free” means zero software-license fees, zero model API fees, and no rented cloud hosting. Hardware, electricity, internet, engineering effort, and enterprise source entitlements are separate. Zero incremental procurement is achievable only if the existing machine is sufficient. No free-tier credits, trial subscriptions, credit card, or paid fallback is part of this design.

## Core stack

| Layer | Selection | License / charge | Purpose |
|---|---|---|---|
| UI | React + Vite + Tailwind CSS | MIT project licenses; no hosted service required | Consultant workspace, evidence drawer, context comparison, and review forms |
| API | Python + FastAPI | Python PSF license; FastAPI MIT | Retrieval orchestration, policy checks, ingestion, and structured responses |
| Database | PostgreSQL | PostgreSQL License | Tickets, passports, outcomes, access metadata, and audit events |
| Semantic search | pgvector extension | PostgreSQL License | Vector similarity search inside the same database |
| Keyword search | PostgreSQL full-text search plus exact identifier fields | Included in PostgreSQL | Technical error identifiers and narrative keyword matching |
| Embeddings | Sentence Transformers + all-MiniLM-L6-v2 | Apache-2.0 library and model | Small, local embedding baseline for English support content |
| Local inference | Ollama open-source runtime | MIT | Serve downloaded model weights on the local machine |
| Language model | Qwen3-4B, quantized; evaluate Qwen3-8B if resources permit | Apache-2.0 model licenses | Explain evidence, summarize tickets, and draft resolution receipts |
| PDF / Word ingestion | pypdf + python-docx | BSD-3-Clause / MIT | Read text PDFs and DOCX without commercial document APIs |
| CSV / JSON ingestion | Python standard library | Included with Python | Load ticket exports and synthetic fixtures |
| File storage | Local filesystem | No separate service | Store permitted source files and extracted artifacts |
| Jobs | Python worker + PostgreSQL job table | Custom code; no additional service | Durable ingestion with retries, leases, and idempotency |
| Testing | pytest + local Playwright | MIT / Apache-2.0 | Retrieval/policy checks and browser workflow tests |
| Packaging | Podman, optional | Apache-2.0 | Repeatable local services, including PostgreSQL with pgvector |

Project and model sources: [React](https://github.com/facebook/react), [Vite](https://github.com/vitejs/vite), [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss), [FastAPI](https://github.com/fastapi/fastapi), [PostgreSQL license](https://www.postgresql.org/about/licence/), [pgvector](https://github.com/pgvector/pgvector), [Sentence Transformers](https://github.com/huggingface/sentence-transformers), [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), [Ollama](https://github.com/ollama/ollama), [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B), [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B), [pypdf](https://github.com/py-pdf/pypdf), [python-docx](https://github.com/python-openxml/python-docx), [pytest](https://github.com/pytest-dev/pytest), [Playwright](https://github.com/microsoft/playwright), [Podman](https://podman.io/).

For scanned documents, add local [Tesseract OCR](https://github.com/tesseract-ocr/tesseract), Apache-2.0, with a compatible local page renderer. Keep scanned PDFs outside the first prototype until that rendering dependency and OCR quality have been tested. pypdf alone does not perform OCR.

For shared deployment, add self-hosted [Keycloak](https://github.com/keycloak/keycloak), Apache-2.0, for identity. A single-user localhost demo can use a fixed demo identity with conspicuous labeling; this is not production authentication. Keycloak does not automatically reproduce SharePoint or SAP permissions.

## Architecture

```text
Browser: React application
            |
            v
FastAPI: identity, applicability, workflow, and citation validation
       |                   |                     |
       v                   v                     v
PostgreSQL + pgvector    Local Ollama         Local files
       ^                Qwen3-4B / 8B            |
       |                                         v
       +-------- Python ingestion worker <--- approved uploads
                 + local embeddings
```

Build the UI into static files and serve them from the application for the local demo. Vite is used during development; it is not a public production server. Keep model and database ports local or on a private container network. On Windows, native Ollama can use the host hardware while Podman hosts PostgreSQL; container-to-host networking must be configured explicitly.

After downloading packages and model weights, the application should operate offline with its local corpus. Disable Ollama cloud features using its documented local-only configuration, configure the application with an explicit local endpoint, and never silently switch to a hosted model. [Ollama FAQ](https://docs.ollama.com/faq).

## Retrieval and intelligence

Extract exact error codes into dedicated fields and split prose at section boundaries. MiniLM is an English short-text baseline: its model card specifies 384-dimensional vectors and default truncation beyond 256 word pieces. Use tokenizer-aware chunks within that limit, with small overlap and parent-section links; never silently truncate whole runbooks. Multilingual retrieval requires a separately evaluated multilingual embedding model. [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).

Run full-text and vector retrieval against authorized records and merge ranked lists with a small custom reciprocal-rank-fusion function. Add deterministic environment checks before displaying a procedure as applicable. PostgreSQL full-text ranking is not BM25; report the implementation accurately. Preserve exact-match handling so punctuation-heavy identifiers do not depend solely on text tokenization.

Use Qwen only to explain the selected evidence and draft structured text. Application code validates prerequisite status, citation IDs, access scope, and allowed actions. A small local model is not a replacement for expert SAP judgment. Measure it on the scenario set and return evidence with an escalation path when generation fails.

| Product capability | Free implementation |
|---|---|
| Environment Lens | Python rules comparing trusted context with passport prerequisites |
| Next Best Question | Expert-authored branches stored as structured records |
| Failure Memory | Outcome events queried by matching environment and procedure version |
| Evidence View | Versioned source sections and validated citation references |
| Resolution Receipt | Qwen draft plus consultant review and append-only outcome events |
| Recurrence Radar | SQL aggregation over reviewed incident families; similarity-assisted grouping later |

No agent framework, graph database, paid reranker, separate search service, or managed vector store is necessary for the first prototype. These features depend primarily on well-structured evidence and application logic.

## Source access under the free constraint

| Source | Zero-subscription prototype route | Limitation |
|---|---|---|
| Historical tickets | CSV or JSON upload, or synthetic incidents | Exporting real records requires existing authorization. |
| Internal knowledge base | Local Markdown, text PDF, DOCX, and text files | Preserve access scope and source version. |
| SharePoint | Permitted document exports in a local source folder | This demonstrates ingestion, not live synchronization or inherited ACL fidelity. |
| SAP repositories | Public links, permitted supplied documents, and explicitly synthetic vendor-style references | Non-public Notes and KBAs still require the relevant entitlement. |

The free core has no mandatory SAP, Microsoft 365, ServiceNow, or Copilot dependency. If those systems are already licensed, their integrations can be assessed separately; a free client library does not make the source service or every API operation free. Keep inaccessible sources disabled rather than creating a dependency on a trial account. See [SAP access documentation](https://help.sap.com/docs/built-in-support/user-guide-for-key-users/76582f630b354f009c4c655c6044b0b5.html) and [Microsoft retrieval licensing](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/overview).

## Hardware planning

These are starting estimates for a single-user demo, not tested minimums:

- With approximately 16 GB system RAM, start with a 4-bit Qwen3-4B model, short context, and one inference request at a time.
- With approximately 32 GB RAM and a suitable GPU, evaluate quantized Qwen3-8B for better answer quality.
- CPU-only inference is a possible fallback, but latency depends heavily on the processor and context size. Do not carry forward the original sub-10-second target as a promise.
- Reserve roughly 20–40 GB of free disk space initially for models, package caches, database, and container images; larger source collections and backups need more.

GPU memory, model quantization, context cache, operating-system overhead, and concurrent ingestion all affect feasibility. Select the final model after measuring the existing machine. If it cannot deliver acceptable generation, retain a working local retrieval-and-rules mode instead of requiring paid inference.

## Costs and release checks

| Item | Charge in this proposal |
|---|---|
| Application software and selected model licenses | RM0 |
| Local model and embedding API calls | RM0 |
| Local database and file storage software | RM0 |
| Cloud hosting and managed services | RM0; not used |
| Optional self-hosted identity and containers | RM0 software fees |
| Existing hardware, electricity, internet, engineering, source subscriptions | Separate; not claimed to be free |

Before accepting the implementation, run the complete demo with network access disabled after setup; check that no remote API credentials are required; record all exact dependency and model versions; retain license notices; and verify that model failures never invoke a paid fallback. This checks the cost constraint as an observable property of the application.

The recommended starting configuration is **React + FastAPI + PostgreSQL/pgvector + MiniLM + Ollama/Qwen3-4B**, with local uploads and deterministic diagnostic rules. Move to Qwen3-8B only if local measurements justify it.
