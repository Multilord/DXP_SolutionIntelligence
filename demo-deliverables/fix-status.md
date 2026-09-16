# Demo readiness follow-up — September 16, 2026

This supplements the original readiness report; it does not replace the inspector's evidence.

## Latest update — hosted blocker resolved

The user confirmed that the Atlas network rule had expired and renewed it. Deployed `/api/health`, `/api/workspace`, `/api/index` and `/api/connectors` now succeed. All seven knowledge sections are indexed with no pending sections.

Deployed SYN-1042 returned the expected cited diagnostic question from a genuine cached Gemini result. Deployed SYN-1045 produced a **fresh**, uncached Gemini quick-reference answer using Atlas Vector Search, selected PASS-HANDOFF and included one cited claim (15.19 seconds in this check). These checks used synthetic content. The hosted AI path is now verified; this does not verify every workflow or external recording-agent capacity. Keep the temporary Atlas rule active throughout recording.

## Verified and addressed

- Local MongoDB connectivity, Gemini generation and Gemini embeddings passed live checks.
- Four bundled synthetic scenarios passed live Gemini generation and real Atlas Vector Search across two runs. Shared incidents/documents were not changed; all rehearsal writes used a temporary local database.
  - Diagnostic: PASS-ROUTE, diagnostic question, 3 cited claims (11.57 seconds).
  - Affirmative observation: PASS-ROUTE, guided runbook, 3 cited claims (9.66 seconds).
  - Unknown checksum: no primary solution, escalation (8.96 seconds).
  - Handover: PASS-HANDOFF, quick reference, 2 cited claims (10.22 seconds).
- Approval alternatives included a historical procedure requiring review and an incompatible embedded-deployment procedure. Changing system revision invalidated the prior result fingerprint.
- Rapid consecutive requests initially hit Gemini rate limits. The remaining scenarios passed after spacing requests. The reusable check now waits 60 seconds between scenarios; this reduces bursts but does not guarantee account quota availability.
- `python -m backend.demo_check` reproduces the check. `--cases knowledge_gap quick_reference` runs a subset. It uses only bundled synthetic content, never real database document text. Its report is `.runtime/demo-check.json` (latest invocation only).
- 40 automated tests passed, including safe, actionable network and permission error responses.
- `/api/model` now explicitly distinguishes a configured key from verified availability with `configured` and `availability_verified` fields. The legacy `available` field remains configuration-based for frontend compatibility.
- Production MongoDB URI and database name exactly match the working local configuration; values were not printed. The temporary comparison file was deleted.
- The production Gemini key differed from the successfully tested local key. The production variable has been updated securely to the tested key; a new deployment applies it.

## Earlier blocker (resolved by the update above)

Vercel database requests return `503 database_unreachable`. Redeployment and a matching URI do not fix Atlas network access. Check Atlas Security → Network Access for expired/missing rules covering the deployment's outbound traffic. Local `/32` access covers only the laptop. Cluster availability or network/TLS restrictions can also cause this class of failure; the exact Atlas rule status still needs confirmation.

Do not disable TLS verification or present local success as deployed success. Once access is restored, verify deployed `/api/health`, `/api/workspace`, `/api/index`, and one real analysis before recording the hosted application.

Claude's recording-agent capacity is an external provider issue, not an application defect. Its recording tools must be checked in Claude; this work cannot guarantee their capacity.

## Demo accuracy

Use the original story only after a rehearsal on the actual recording target. Say “retrieved knowledge passages,” not that the entire knowledge base is sent to Gemini. Reviewed procedures are synthetic examples, not operational SAP instructions. Capture/review/publication have automated workflow coverage; their complete live Gemini reuse sequence was not part of this four-scenario check.
