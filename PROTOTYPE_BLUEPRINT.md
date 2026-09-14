# Solution Atlas Prototype Blueprint

For implementation architecture, database tables, middleware, API contracts, and build order, follow [BUILD_PIPELINE.md](BUILD_PIPELINE.md). It specifies local inference only.

Technology constraint: implement using the free local stack in [FREE_TECH_STACK.md](FREE_TECH_STACK.md). Use local inference and permitted uploads; no paid API, cloud subscription, or trial credit is required.

## Purpose and scope

Demonstrate that an assistant can select a better-supported next action by combining incident context, environment applicability, source evidence, and confirmed outcomes. This specification accompanies the research report. It describes proposed behavior and synthetic examples; it is not a deployed application or an operational SAP runbook.

The prototype should make one proposition testable: **a similar historical ticket is useful only when the relevant conditions also match.**

Build a consultant workspace with three incident scenarios, four clearly labeled source categories, and a reproducible retrieval-and-ranking pipeline. Use local fixtures for connectors. A real model may explain retrieved evidence, but a deterministic policy enforces access and applicability. If the entire demo is scripted, label it a concept simulation rather than AI inference.

## 1. Five-minute demonstration

All incident identifiers, configuration flags, counts, and resolution events below are invented for product demonstration. The `demo_route_enabled` setting belongs to a mock application; it is not an SAP configuration instruction.

| Time | Presenter action | Visible response | Point established |
|---|---|---|---|
| 0:00–0:35 | Open SYN-1042: an approval workflow fails after a deployment. | Atlas extracts symptom, affected system, release, and onset, with source labels and editable unknowns. | No separate search session is required. |
| 0:35–1:15 | Inspect similar incidents. | A highly similar old case appears in the authorized evidence list, but its procedure is marked inapplicable because its deployment model differs. | Text similarity is separated from applicability. |
| 1:15–2:00 | Answer “Does the same action work through the alternate application path?” with “Yes.” | An authored diagnostic branch reduces the priority of a general user-permission hypothesis and favors checking the application route. It explains that this is evidence, not conclusive proof. | One useful question narrows the investigation. |
| 2:00–2:45 | Open the recommended passport. | Show a current internal guide, a prior comparable case, the relevant source passages, and a missing precondition. | Recommendation is inspectable and conditional. |
| 2:45–3:30 | Run a read-only mock check. | Fixture reports `demo_route_enabled=false`; the procedure becomes eligible for review. A recovery checklist is displayed. | Facts change eligibility; the model does not invent system state. |
| 3:30–4:15 | Click “Simulate approved fix” in the mock environment, then “Verify.” | Only the mock flag changes; a simulated workflow check passes. The UI keeps the simulation label visible. | The demo includes an observed outcome without implying a production change. |
| 4:15–5:00 | Review the resolution receipt. | Draft links actions, source versions, and verification. A local outcome is appended; an existing passport is proposed for update. | Support work produces reusable evidence. |

The payoff line is: **“Atlas found a similar case, spotted why its fix did not apply, and used one observation to choose a better next step.”**

## 2. Screens and interaction behavior

### Consultant workspace

Use a three-column desktop layout: incident context on the left, recommendation and diagnostic action in the center, and evidence on the right. Keep the center readable when source previews open. On smaller screens, switch to labeled context, action, and evidence tabs.

The context panel shows product family, release, deployment type, business process, affected scope, time of onset, and recent change. Each field has a provenance label: imported, observed, consultant-confirmed, or unknown. Editing context triggers a new applicability assessment and adds a local audit event.

The center panel shows one primary next action and at most two alternatives. Prefer “Check the application route” over a premature root-cause declaration. It should state what is known, what is missing, why the action is useful, and what result would change the path.

Use evidence status text rather than an unexplained confidence percentage:

- **Supported:** required prerequisites are verified and supporting sources are available.
- **Needs a check:** a material condition is unknown.
- **Not applicable:** a known hard prerequisite conflicts.
- **Needs expert review:** evidence is missing, contradictory, or outside supported scope.

Do not use color as the only indicator. All controls need keyboard access, visible focus, accessible names, and readable contrast.

### Evidence drawer

Clicking a citation opens the exact fixture document section, version, and source category. Display why the passage supports the action and whether that link is an authored mapping or generated explanation. Historical cases show environment differences and outcome status.

Show a contradiction as two scoped claims, not a merged instruction. An authorized but inapplicable source can be inspected for context. Unauthorized content must be excluded from retrieval, previews, counts, and exports; the interface should not reveal its title or existence.

### Resolution receipt

Show editable fields for observed issue, confirmed context, attempted actions, result, validation method, outstanding follow-up, and linked passport version. The consultant can choose confirmed, failed, pending validation, or unknown. A successful mock check does not imply sustained real-world recovery.

Saving a local receipt appends an outcome event. Material passport changes remain drafts until a simulated reviewer approves them. Label approval simulation clearly. Export a draft Markdown receipt if useful; do not automatically publish it to an enterprise knowledge base.

### Knowledge maintenance view

Provide a small queue containing one outdated-source candidate, one conflicting-procedure candidate, and one repeated incident family. Each row has an owner, supporting evidence, and a proposed disposition. Avoid an elaborate dashboard full of invented operational KPIs.

## 3. Synthetic scenario pack

| Scenario | Fixture evidence | Required behavior |
|---|---|---|
| A: Applicable fix hidden behind a similar case | A legacy procedure, a current route procedure, a deployment event, and a diagnostic observation | Reject the legacy action for a verified mismatch; ask a useful question; recommend a conditional check. |
| B: Tempting workaround already failed | Similar symptoms, an attempted restart with no recovery, and an approved diagnostic guide | Surface the prior failed attempt in comparable conditions; do not count a merely suggested restart as failure. |
| C: Unknown incident with conflicting evidence | Sparse notes, conflicting guidance with overlapping scope, and no confirmed resolution | Withhold a fix, show evidence gaps, and generate an escalation packet. |

Add a fourth small request fixture if time permits: access provisioning should resolve to an approved mock catalog flow with required entitlement and approval, rather than enter the incident diagnosis workflow.

Suggested corpus: 30–50 short synthetic ticket records, 8–12 internal articles, 4–6 SharePoint-style documents, and several clearly labeled synthetic vendor-style references. Include duplicates, failed attempts, obsolete versions, and restricted documents. These quantities are build estimates, not sufficient training or validation data.

Do not invent real SAP Note numbers or imply synthetic text came from SAP. Use identifiers such as `SYN-VENDOR-003`, with an explicit synthetic label. Public SAP documentation may be linked separately where it supports a genuine product fact.

## 4. Minimum data model

```text
Incident
  id, tenant_id, client_id, opened_at, title, symptoms, request_type
  environment_facts[{name, value, source_id, observed_at, status}]
  observations[], permitted_principals[], fixture_label

EvidenceDocument
  id, tenant_id, client_id, source_type, source_uri, version
  available_at, updated_at, content_hash, access_policy_id
  sections[{id, text}], status, fixture_label

SolutionPassport
  id, version, problem_signature, owner, lifecycle_state
  prerequisites[], contraindications[], diagnostic_branches[]
  steps[{id, action, expected_result, stop_condition, evidence_refs[]}]
  validation_checks[], recovery_guidance, supersedes_id

OutcomeEvent
  id, incident_id, passport_id, passport_version
  action_status, environment_snapshot, validation_result
  observed_at, confirmed_by, reopened_at, evidence_refs[]

Recommendation
  id, incident_id, environment_snapshot_hash, candidate_ids[]
  applicability_checks[], next_question, next_action
  evidence_refs[], unsupported_claims[], policy_decision, created_at
```

Store missing values explicitly; do not fill them with plausible model guesses. Evidence references identify an actual section and version. A generated explanation cannot introduce a nonexistent document identifier.

## 5. Behavior and API contract

Suggested internal API surface:

| Endpoint | Purpose | Guardrail |
|---|---|---|
| `GET /incidents/{id}` | Load authorized context | Scope comes from server identity. |
| `POST /incidents/{id}/recommendations` | Retrieve evidence and assess candidates | Reject inaccessible incident IDs and stale context revisions. |
| `POST /incidents/{id}/observations` | Append a diagnostic answer | Validate field type, actor, and current investigation state. |
| `GET /evidence/{id}/sections/{section}` | Show cited text | Recheck access; expose only permitted metadata. |
| `POST /incidents/{id}/outcomes` | Save a reviewed receipt | Idempotency key prevents duplicate success counts. |
| `POST /demo/reset` | Reset synthetic state | Available only in explicit demo mode. |

The client must not set its own tenant or bypass policy by submitting a different client identifier. In a local fixture implementation, simulate two identities in a server-controlled session; document that this proves application behavior, not enterprise SSO integration.

Recommended investigation states are `context_needed`, `retrieving`, `diagnostic_needed`, `recommendation_ready`, `review_needed`, `validation_pending`, and `closed`. A context edit invalidates previous eligibility. A timeout preserves the incident and allows retry without duplicating an outcome.

Use an explicit maximum of three diagnostic rounds for the demo. When the limit is reached, create an escalation packet with confirmed context, attempted actions, source evidence, and unanswered questions. This makes the failure path as reviewable as the successful path.

## 6. What should actually work

| Component | Demonstrator requirement | Production work remaining |
|---|---|---|
| Source adapters | Load local fixture records with visible source labels | Authenticated APIs, synchronization, deletions, and operational monitoring |
| Retrieval | Search the fixture corpus and return traceable sections | Scale, indexing operations, and enterprise ACL correctness |
| Applicability | Execute deterministic prerequisite checks | Domain coverage and authoritative system facts |
| Diagnostic questioning | Follow authored conditional branches | Evaluation of adaptive question selection |
| Explanation | Real grounded generation or clearly labeled scripted text | Model selection, claim validation, latency, and monitoring |
| Resolution receipt | Persist local outcome and create a draft update | Enterprise knowledge workflow and longitudinal confirmation |
| Identity | Demonstrate fixture isolation | SSO, group semantics, revocation, and tenant policy |
| Remediation | Change only mock application state | Separate approvals, change integration, execution gateway, and recovery design |

## 7. Acceptance tests

The demonstrator is complete when each of these can be shown reproducibly:

1. A paraphrased symptom retrieves an applicable candidate while exact identifiers remain searchable.
2. A known release or deployment mismatch blocks the corresponding action regardless of textual similarity.
3. Missing prerequisites produce “Needs a check,” not “Supported.”
4. Different diagnostic answers produce the intended different next action.
5. Every displayed citation opens the exact referenced fixture section and version.
6. A document containing instructions to ignore policy cannot trigger a tool call or disclose restricted data.
7. Changing fixture identity removes restricted material from retrieval, source previews, counts, and receipt exports.
8. A deleted or superseded source invalidates affected cached recommendations.
9. Conflicting evidence and unknown scenarios produce a useful escalation packet.
10. Repeated submission of the same outcome does not increase the success count twice.
11. Failed, unattempted, and unverified outcomes remain distinct.
12. Replay evaluation excludes the test ticket’s future resolution and later documents.
13. Keyboard-only users can complete the primary scenario and inspect evidence.
14. Every simulated integration and result is visibly labeled.

Track pass/fail results in a run log with fixture version, application revision, and model configuration if a model is used. Do not present these tests as measured production outcomes.

## 8. Suggested delivery order

First agree on the three narratives and write the fixture evidence with a support specialist. Next implement the data model, retrieval, and applicability checks before polishing the interface. Add the evidence drawer and diagnostic branch, then the resolution receipt and unknown-case path. Finally run the acceptance suite and rehearse the demonstration from a clean reset.

The prototype should end with a concrete decision: whether environment checks and evidence-guided diagnosis improve action selection enough to justify a scoped live pilot. Visual polish helps communicate that result, but the decisive artifact is a traceable recommendation that changes correctly when the facts change.

## 9. Additional Aegis-inspired demonstration scenes

These additions adopt the reviewed proposals without adding Claude or other hosted inference. See AEGIS_IDEAS_REVIEW.md for the assessment and BUILD_PIPELINE.md section 17 for the implementation contract.

### Scene A: a fix becomes stale after a relevant change

Use a synthetic system `SYN-FIN-01` with a procedure verified on June 10, 2026. Search an applicable incident and show the verification record. Add a mock applied change effective August 15 that affects one of the procedure's prerequisites; evaluate at September 15. Show “Relevant system change since verification — revalidation required,” the specific change, and the affected condition.

Add an unrelated mock change on another system and demonstrate that it does not affect this candidate. Record a simulated expert revalidation against the current context and show eligibility restored only for the validated scope. A simple age-based counter must not drive this demonstration. All change labels and environment versions are synthetic, not real SAP patch guidance.

### Scene B: close a knowledge gap visibly

Search a deliberately unsupported issue and show “No usable precedent in the available knowledge,” with the actual gap reason. Resolve the mock case manually, click “Capture verified resolution,” and confirm the prefilled actions and validation. Wait for the displayed local indexing job to complete.

Show the capture as unreviewed to the author/reviewer, then approve it using the demo review role. Search a paraphrased equivalent issue and retrieve the newly published source. The UI should describe this as an indexed knowledge update, not model retraining. Keep duplicate-capture and source-permission controls active.

### Scene C: the answer format fits the work

Use three or four compact examples: an informational quick reference, an approved multi-step runbook, a case needing one observation, and an escalation with no supported procedure. Show computed evidence chips for error identifier, component, and environment alongside freshness state. Operational steps come from approved records; local Qwen supplies concise explanation.

Do not use the proposed 84–94% confidence values, under-two-second response promise, or 15–20-minute manual-search baseline as measured facts. Display actual timing separately for retrieval and validated generation. Replace “Apply Solution” with “Review resolution plan” unless a visibly labeled mock action is being demonstrated.
