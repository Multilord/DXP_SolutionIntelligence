# Aegis Proposal Review and Adopted Improvements

## Decision

Adopt all four product ideas, with the strongest new work focused on change-aware solution validity and an explicit knowledge-gap lifecycle. Keep React, FastAPI, PostgreSQL/pgvector, local MiniLM, and Ollama/Qwen3-4B. The attachments' Claude/API architecture is a proposal to assess, not a change to the no-hosted-inference requirement.

The repository currently contains specifications, not an application. These improvements are incorporated into BUILD_PIPELINE.md and PROTOTYPE_BLUEPRINT.md as requirements and acceptance scenarios; they have not been implemented or tested in software. Solution Atlas remains the working project name; Aegis is the name in the supplied proposals.

## Reviewed material

- `solution-intelligence-engine-proposal.md (1).pdf`, four pages: positioning, synthesis, feedback, knowledge gaps, and a staged demo.
- `Untitled document (1).pdf`, five pages: support-console mockup, effectiveness comparisons, and synthetic data.
- `aegis-technical-build-plan.md`: schema, TF-IDF retrieval, signal scoring, upgrade penalties, capture, and API synthesis.
- The four USPs supplied in the conversation.

The documents contain useful design proposals, but no measured results for this device or evidence that competitors lack the features. Their 15–20-minute manual-search baseline, under-two-second synthesis, and 80–94% confidence/effectiveness examples are not adopted as project facts.

## What changes relative to the current design

| Proposal | Existing coverage | Substantial addition | Decision |
|---|---|---|---|
| Temporal Relevance Decay | Environment Lens, source versions, stale-result handling | Scoped system-change events, validation history, impact assessment, revalidation queue | Adopt change-aware validity; decay can only be a secondary ranking heuristic |
| Confidence + Evidence Trail | Evidence View and citation validation | Computed match chips, mismatches, and compact rationale panel | Adopt; no uncalibrated success percentage |
| Knowledge Gap Capture Loop | Outcome receipts and reviewed updates | First-class gap records, ownership, closure criteria, before/after search demo | Adopt with review state and indexing visibility |
| Answer-type synthesis | Diagnostic questions, procedures, escalation | Typed response contract and different UI layouts | Adopt; deterministic policy controls format, local Qwen drafts prose |

## 1. Change-aware validity: the highest-value addition

Elapsed time alone does not establish whether a fix remains applicable. A relevant configuration change can invalidate a solution overnight; an older guide can remain valid after successful revalidation. Add a timeline for each system instance and component so the product can explain this history.

Store effective and recorded dates, applied/reverted/planned status, affected configuration areas, before/after state, provenance, and any explicitly reviewed impact on a procedure. Assess effective changes after the procedure's latest valid verification in a comparable environment. Unrelated system/module changes must not penalize it. An unknown impact requires review; a known incompatibility blocks the action; revalidation can restore applicability for the validated scope.

| State | Meaning | Behavior |
|---|---|---|
| Verified for current context | Preconditions and validation cover the relevant current state | Eligible, subject to ordinary evidence checks |
| Relevant change since verification | Later scoped change; effect not established | Ask for revalidation; do not present as verified |
| Known incompatible | Current state violates a hard prerequisite | Exclude the operational action |
| Context/history incomplete | Required facts or change coverage are missing | Request missing information |
| No intervening relevant change recorded | Available history has no relevant applied event | Display a limited observation, not a guarantee |

The supplied `0.15 * number_of_upgrades` penalty is too crude: an unrelated upgrade can demote a valid fix, while a dangerous fix can remain eligible because its initial score was high. Replace it with explicit applicability states. A ranking bonus or penalty must never override a hard block.

The best demonstration adds a scoped mock upgrade between searches. The same candidate changes from supported to needing revalidation, with the affected condition shown. An unrelated upgrade leaves it unchanged. A mock expert revalidation restores eligibility only for that scope.

## 2. Evidence Trail: show observable reasons

Compute match chips in application code: exact error identifier, component, environment, and symptom overlap. Include unmatched and unknown facts. Link each important procedural step to its actual section and version.

Separate retrieval match, applicability/freshness, and observed outcomes. A weighted relevance score is not a calibrated probability of successful resolution. Prefer labels and comparable-case counts. If a numeric index is later introduced, label it a ranking index and document its calculation. Do not display a model's internal reasoning as an evidence trail.

Use source colors with accessible text labels. Color indicates origin, not reliability. Source permissions apply to chips, counts, previews, and generated text. Show historical handling-time statistics only with measured denominators and a definition of active effort versus elapsed resolution time.

## 3. Knowledge Gap Capture: make the loop operational

A weak result does not prove that nobody knows the answer. Distinguish missing context, incomplete ingestion, temporary source unavailability, conflicting procedures, and no usable precedent in the accessible corpus. Never disclose that restricted records exist.

Create a gap with reason, incident family, owner, scope, context, and lifecycle. The one-click action becomes **Capture verified resolution**: prefill known facts, then ask the consultant to confirm actual actions and validation. Save an outcome and knowledge draft. After indexing, the author and permitted reviewers may find it in a clearly marked unreviewed view; approval promotes the procedure into normal recommendations.

Show the loop transparently: search without a usable precedent → capture a synthetic resolution → wait for indexing → approve as a demo reviewer → search a related query → retrieve the new source. This updates the index and knowledge records; it does not retrain the model.

Track time to an approved searchable answer and the proportion of eligible gaps closed within a chosen window. Keep source-outage and missing-context cases separate so the metric reflects actual knowledge improvement.

## 4. Answer-type synthesis: low cost, visible benefit

Use quick reference, guided runbook, diagnostic question, and escalation response forms. Intent suggests a format; evidence, prerequisites, and action risk determine what is allowed. A familiar-looking production change still needs an approved runbook. Missing conditions trigger diagnosis; unresolved incompatibility or conflict triggers review/escalation.

Qwen supplies concise explanation inside the selected form. Approved action IDs and ordering come from the database. Escalation teams and contacts must come from maintained, authorized routing records. Never invent them when missing.

Multiple sources may corroborate the same procedure. Do not merge unrelated ticket steps into an unreviewed operational runbook. A novel combination requires a new reviewed passport version.

## Additional ideas worth retaining or correcting

The compact answer/investigate/capture interface is useful for the core demonstration. Design synthetic cases deliberately around success, obsolete guidance, unrelated changes, conflicts, and a gap. Do not treat synthetic performance as enterprise benchmark evidence.

Keep thumbs-up/down as usability feedback and a review signal. Store attempted/confirmed/failed outcomes separately. Directly multiplying by a helpfulness ratio creates popularity and small-sample problems; a downvote must not override applicability or rewrite operational truth.

Retain PostgreSQL and local embeddings. TF-IDF is a valid lexical baseline but duplicates an already planned local retrieval path, and scikit-learn is still a software dependency. In the supplied technical plan, writing a captured ticket to SQLite does not update the frozen TF-IDF matrix: index refresh is necessary before the next query can find it. Our worker explicitly records indexing completion.

Replace the mockup's “Apply Solution” with “Review resolution plan” and “Record outcome.” Mock execution must stay visibly simulated. Any precomputed explanation must be labeled and invalidated when context, source policy, or change history changes.

## Priority and feasibility

1. Scoped change history and revalidation: strongest new domain capability.
2. Explicit gap lifecycle and capture/reuse demonstration: strongest visible learning loop.
3. Typed response forms: substantial usability benefit with limited complexity.
4. Computed evidence chips and outcome comparisons: clarity on top of the existing evidence model.

All four fit the local stack and current hardware because they primarily add structured data, deterministic rules, and UI states. The main challenge is reliable change and validation data, not a larger model or GPU.
