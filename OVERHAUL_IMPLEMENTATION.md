# SolutionAtlas v2: investigation and verification workspace

This implementation follows the interview-summary overhaul. The default UI is v2. The previous UI remains available at `?legacy=1` for regression reference; its unscoped APIs are disabled whenever protected v2 access is enabled. Existing v1 data is not migrated or deleted. V2 persists in a separate `atlas_records` collection/table.

## Implemented

- Customer-scoped investigations and direct record access, with separate shared generalisations.
- Explicit platform incompatibility, uncertain release/component/environment compatibility, supersession, procedure approval, and revision-specific current-system verification.
- Gemini embeddings plus exact local vector comparison over the bounded authorised corpus; lexical/error signals augment ranking. This v2 path does **not** use the old Atlas vector index. Database persistence still supports Atlas.
- Structured Gemini relevance/cause assessments, exact-quote validation, source conflicts, diagnostic questions, and a second grounding pass. AI errors fail explicitly. A separately labelled rules preview never claims AI ran.
- Private incident capture, notes-to-draft AI extraction, technical review, separate sharing review, publication, and outcomes.
- Reviewers must verify the current incident context before an approved procedure can become executable guidance. Matching versions and closed tickets alone are insufficient.
- Closed-incident recurrence groups, workaround counts and existing problem links. Exact error/component groups are supplemented by grounded Gemini grouping suggestions over private incidents, including closed cases. Neither establishes a common root cause.
- Scoped change-impact suggestions with quotes and grounding; no automatic validity changes.
- Administrator JSON import, basic pattern masking, source retraction API, and versioned indexing.
- Server-side role checks, tenant membership, audit records, and stale analysis rejection.
- Corrected synthetic runtime corpus: 81 records. Ground truth and relevance labels stay in the evaluation dataset, outside the application corpus.
- Evaluation report in Administration. The default report compares keyword vs applicability-rule ranking, and explicitly does not claim live AI accuracy.

## Run

Use the existing application commands (`npm run build`, then `python -m backend.run`). V2 seeds its synthetic fixture on the first workspace request. For an isolated local rehearsal, set `DATABASE_BACKEND=sqlite`, `VECTOR_BACKEND=local`, and `ATLAS_STORAGE_DIR` to a new local folder before starting.

1. Select a synthetic customer and open an incident.
2. Use **Rules preview** to inspect matching evidence without provider calls.
3. Switch the simulated role to reviewer; Administration -> Build next batch until remaining reaches zero. This uses Gemini quota.
4. Run **Analyze with Gemini**. Inspect dimensions, exact evidence, questions and conflicts.
5. Record observations; analyze again. Previously saved results are stale after source/context updates.
6. Capture a resolution from any incident. In Review centre, approve technically. Shared drafts require a second explicit generalisation review.
7. Reindex newly published knowledge. Reviewers can record current-system verification from an approved candidate; then reanalyze.
8. Use Aurora's Problem insights to see five workaround closures and the linked problem record.

## Access modes

Default: clearly labelled **synthetic demo**. Customer/role switching simulates users and grants access only to records marked synthetic. Never enter confidential data in this mode.

Protected prototype: set `ATLAS_V2_PROTECTED=true` and configure `ATLAS_ACCESS_TOKENS` as a JSON object. Each key is a random token of at least 32 characters and its value contains `user`, `tenants` (exact account names), and `role` (`consultant`, `reviewer`, or `admin`). Use a distinct token for each identity. Values stay server-side. The UI accepts a token in memory; it is not stored in localStorage. Account headers cannot change the identity's assigned membership or role. Missing credentials fail closed. Unscoped v1 APIs return 410.

This is a service-token prototype, not Entra SSO, MFA, or source-level ACL synchronisation. The provider boundary is injectable, but only Gemini is implemented. Azure deployment and authentication require approved tenant details and integration work.

## Import contract

Administration accepts a JSON object containing a `records` array (1-50 records). Each record has `external_id`, `title`, `content`, `platform`, `release`, `source`, and optional `component`. External identity is scoped by customer and source. Reimport increments the version and invalidates embeddings. Imports are private, unverified evidence, never approved procedures.

Pattern masking covers email addresses, IPv4 addresses and common key/password assignments only. It is not comprehensive anonymisation. Shared publication has human technical and sharing checks plus limited automated detection; it must not be described as guaranteed de-identification.

## Dataset corrections

`python -m backend.prepare_overhaul` regenerates fixtures from untouched Overhaul inputs. Private customer records remain private. Standard-case synthetic derivatives are separate shared records. Q03 and Q07 use explicit curated generalisations instead of another customer's private tickets. Q09 distinguishes the primary vendor-maintenance precedent from a conditional approval issue. Customisation flags are normalised; service requests have their own quality label. Runtime drops ground_truth, scenario_group and change relevance labels. CSV omits change history and is not canonical.

Synthetic guidance requires an SAP SME's review before operational use. Historical fixtures are evidence, not preapproved runbooks. Generic cross-release guidance remains uncertain until validated for the incident.

## Verification

`python -m unittest discover -s backend/tests -v`

`npm run build`

`python -m backend.evaluate_overhaul` creates the offline report shown in Administration. It uses isolated SQLite storage and does not mutate the application database. Use `--ai --cases SYN-Q04` for an optional live synthetic evaluation (consumes Gemini quota). Do not treat the ten development fixtures as a held-out benchmark or an estimate of staff-hours saved.

## Remaining enterprise work

- Entra SSO and source ACL synchronisation, approved hosting/network configuration.
- Live Solution Manager, Confluence and licensed SAP KBA integrations; v1 adapters are not silently exposed as tenant-safe v2 connectors.
- Complete secret/PII detection, source owner sharing authorisation, and security review.
- Scalable tenant-filtered vector indexes and background ingestion; current retrieval reads a bounded corpus.
- Rich incident/problem/change imports, automatic refresh/deletion events, and notifications.
- Operational evaluation with unseen SME-reviewed examples and larger incident corpora.
- Independent live verification of every AI workflow and deployed service connectivity.

No automatic SAP changes, operational approval management, workload prediction, or proven business savings are claimed.

## Latest validation (11 October 2026)

- Full backend suite: 71 passing tests. After the final grounding-schema change, all 17 overhaul-specific tests passed again.
- Production frontend build passed; the retained legacy UI contributes to the existing bundle-size warning.
- Live Gemini synthetic case SYN-Q04 retrieved GEN-SYN-H016 and passed grounding. It returned diagnostic questions, not the fixture's quick-reference label, because the historical procedure has not been approved and verified for this incident. The mismatch remains visible in evaluation-live-report.json.
- Live UI clustering of Aurora synthetic incidents passed grounding and grouped the five recurring job cancellations, plus a related new-company-code configuration pair.
- Offline ranking found an expected precedent in the top three for all nine positive development cases. This is a development-fixture check, not production accuracy or savings evidence.
- Local preview uses isolated SQLite storage. This overhaul has not been deployed or verified against the live MongoDB instance. Other AI workflows retain unit coverage but still need independent live acceptance testing.
