# AI-Powered Solution Intelligence Engine

Implementation update: the project now requires a free local stack. The decision in [FREE_TECH_STACK.md](FREE_TECH_STACK.md) supersedes the managed-service stack candidates in this report. The broader research and product recommendations remain relevant.

## Executive recommendation

Build **Solution Atlas**, an assistant embedded in the consultant’s incident workspace that recommends the best-supported next action for the specific system being investigated. Its central object is a reusable **Solution Passport**: a versioned record of the problem, applicable environments, diagnostic evidence, resolution procedure, known failures, validation checks, and observed outcomes.

The defining product promise is: **“Find what worked, verify it fits, and preserve what you learn.”**

The strongest demonstration is a case where the most textually similar historical solution is wrong for the current environment. Atlas identifies the mismatch, asks one useful diagnostic question, surfaces a better-supported procedure, and records the confirmed result. This makes the value visible in a way that a fluent answer or a list of search results cannot.

This is a recommended product strategy, not a claim of a novel invention or demonstrated competitive superiority. Search, incident summaries, contextual recommendations, and log-assisted troubleshooting already exist. The opportunity is to combine environment applicability, disconfirming evidence, and verified outcomes across the organization’s fragmented sources.

The research covers public primary sources available on September 15, 2026. No internal tickets, SAP entitlements, SharePoint tenant, operational baseline, or production environment were available. Product capabilities are distinguished from proposed features; numerical targets and delivery estimates below are planning assumptions. The accompanying prototype blueprint specifies a demonstrator; no functioning application is delivered with this research.

## 1. What the evidence supports

### Existing products establish a demanding baseline

| Platform or practice | Verified capability | Consequence for Atlas |
|---|---|---|
| ServiceNow Now Assist | Incident investigation can retrieve knowledge articles and similar resolved incidents and recommend resolution steps. Current documentation also describes incident summaries and proposed next steps. | A generic incident copilot is insufficient differentiation. Evaluate native capabilities before building overlapping features. |
| SAP for Me | Unified knowledge search spans SAP resources and can present generated answers with source results and product/component filters. | Integrate with SAP’s knowledge experience where possible; do not recreate its entire repository. |
| SAP troubleshooting tools | Support Log Assistant matches support files against known issues. ANST uses issue replication to search for Notes. Note Assistant recognizes dependencies involving Notes, support packages, and implemented modifications. | Even context-aware SAP troubleshooting is established. Add customer-specific history, cross-system context, and outcome tracking. |
| Atlassian Jira Service Management | Its virtual service agent generates answers from linked knowledge bases, particularly for informational questions and documented procedures. | Distinguish consultant diagnosis from employee self-service. |
| Glean | Documentation describes support-context search and resolution assistance. The current page announces retirement of its previous embedded ServiceNow experience in favor of a browser extension sidebar. | Cross-repository search is a buy-versus-build option. Validate the supported integration path rather than copying older examples. |
| Knowledge-Centered Service (KCS) | Knowledge capture, reuse, and improvement occur in the support workflow; aggregate experience informs organizational improvement. | Make learning part of incident resolution, with ownership and review. |

Sources: [ServiceNow investigation workflow](https://www.servicenow.com/docs/r/xanadu/it-service-management/now-assist-for-it-service-management-itsm/now-assist-itsm-aiagents-incident-resolver-workflow.html), [ServiceNow incident experience](https://www.servicenow.com/docs/r/it-service-management/generating-ai-native-itsm.html), [SAP Knowledge Tab](https://support.sap.com/content/s4m/help/support/search.html), [SAP troubleshooting tools](https://support.sap.com/en/tools/troubleshooting.html), [Atlassian AI answers](https://support.atlassian.com/jira-service-management-cloud/docs/atlassian-intelligence-answers-in-the-virtual-agent/), [Glean integration documentation](https://docs.glean.com/administration/platform/embedded-integrations/glean-in-service-now), [KCS practices](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/041).

These are documented capabilities, not independent performance comparisons. Enterprise editions, tenant settings, and negotiated contracts may change what a particular team can use. The absence of a feature from this comparison does not establish that a vendor lacks it.

### AI assistance has credible value, but transfer to SAP support must be tested

Brynjolfsson, Li, and Raymond’s revised study of 5,172 customer support agents reports a 15% average increase in issues resolved per hour. Effects differed by worker experience; the most experienced and skilled workers saw small speed gains and small quality declines. The study supports testing AI assistance, especially for less experienced consultants, but does not justify promising a 15% improvement in SAP incident resolution. Its setting, task mix, and intervention differ. [Generative AI at Work, revised November 2024](https://arxiv.org/abs/2304.11771v2).

Microsoft’s research on agents for root cause analysis supports collecting diagnostic evidence beyond incident prose. Its evaluation found increased factual accuracy relative to strong baselines, while adding incident discussions alone did not significantly improve performance. This favors purposeful evidence collection over indiscriminately sending more text to the model. Cloud incident research is useful methodological evidence, not an SAP benchmark. [Exploring LLM-based Agents for Root Cause Analysis](https://www.microsoft.com/en-us/research/publication/exploring-llm-based-agents-for-root-cause-analysis/).

Retrieval-augmented generation supplies external information to a language model and was demonstrated on knowledge-intensive NLP tasks. It is a foundation for current, attributable answers, but it does not establish that a retrieved fix is operationally appropriate. [Lewis et al., Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401).

### The actual product problem is selecting an applicable action

The following failure modes are design hypotheses to validate against real incident samples:

| Failure mode | Why search alone is inadequate | Required behavior |
|---|---|---|
| Identical symptoms, different causes | “Access denied” may arise at different layers. | Separate hypotheses using diagnostic evidence. |
| Similar system, different release | Historical procedures may target another product version or deployment model. | Explicit applicability checks; unknown is not compatible. |
| Closed ticket, weak resolution | “Fixed” or “restarted” does not establish cause or lasting recovery. | Keep low-quality tickets as context; do not promote them into trusted procedures. |
| Several copied tickets | Duplicate records can inflate apparent support. | Count independent incidents and identify shared outages. |
| Contradictory sources | A newer document may have a different scope; an older local workaround may still apply. | Present the scope of the disagreement and route unresolved conflicts to an owner. |
| Repeated failed attempts | Success-only knowledge hides useful disconfirming evidence. | Record failure with its environment and observed result. |
| Missing knowledge | A persuasive answer can conceal inadequate evidence. | Ask for the next useful observation or prepare an escalation packet. |

## 2. Product concept and consultant experience

### A focused first customer and workflow

Start with one support team, one client boundary, and one well-instrumented SAP application family. Good candidate categories are recurring application access issues, integration failures, and batch processing incidents with documented outcomes. These are proposed starting points; choose the actual category after measuring volume, recurrence, evidence quality, and operational risk.

The consultant opens a ticket and sees a compact panel containing the current issue, confirmed system context, leading candidate, evidence gaps, and next diagnostic action. Sources open alongside the recommendation. The consultant can correct extracted facts before those facts affect applicability.

Distinguish incidents from service requests early. An incident asks how to restore service; a service request may already have a catalog procedure, entitlement requirement, and approval path. For requests, recommend the approved fulfillment workflow and required information rather than inventing a root cause. For widespread incidents, link to the coordinated incident response so consultants do not independently repeat changes.

### The Solution Passport

Each passport should answer seven questions:

1. **What problem does it address?** Symptoms, exact error identifiers, business process, and candidate cause.
2. **Where does it apply?** Product, release, deployment model, component, configuration constraints, and relevant customizations.
3. **What evidence supports it?** Source passages, independently resolved incidents, diagnostic observations, and reviewer status.
4. **What must be checked first?** Preconditions, required privileges, contraindications, and missing observations.
5. **What is the procedure?** Ordered actions, expected results, stop conditions, change requirements, and recovery guidance where available.
6. **How is success established?** Technical check, business outcome, observation window, and reopening status.
7. **Who maintains it?** Owner, version, source revision, last review, supersession, and access policy.

This is a structured knowledge record, not a generated summary saved without review. Several passports may share a symptom but differ in applicability. A reusable procedure and an observed application of that procedure are separate records, preventing one successful use from changing the meaning of the procedure itself.

## 3. Features that make the concept stand out

### 3.1 Environment Lens — show why a solution fits

Compare the current environment with each candidate’s prerequisites. Present **verified match**, **known mismatch**, or **unknown** for each important field. A verified hard mismatch removes the action from executable recommendations; missing information leads to a diagnostic question or a conditional candidate.

The memorable interaction is an environment toggle in the demo: changing the system release or deployment type visibly changes the recommendation and explains the reason. In production, environment facts must come from trusted inventory, approved diagnostics, or consultant confirmation with provenance.

The novelty hypothesis is the combination of applicability and organization-specific outcome history. SAP already has dependency-aware tools, so the pitch must not claim that checking SAP dependencies is new. Atlas should hand off to supported SAP tooling for authoritative checks rather than pretending its extracted metadata replaces them. [SAP troubleshooting tools](https://support.sap.com/en/tools/troubleshooting.html).

### 3.2 Next Best Question — reduce uncertainty before recommending a change

When two causes remain plausible, ask the lowest-cost question whose answer would change the next action. A question might distinguish one user from all users, one application path from another, or failure before versus after a deployment. Explain why the answer matters.

Implement the first version with expert-authored decision branches attached to passports. Later, estimate expected information gain over a calibrated hypothesis distribution and subtract collection cost and risk. A model should not improvise unlimited investigation loops. Set a step budget and escalate when the available observations cannot separate the candidates.

**Demo moment:** one answer removes an attractive but unsupported fix and reveals a more appropriate diagnostic path. Measure questions-to-useful-action and unnecessary actions avoided, rather than conversation length.

### 3.3 Failure Memory — preserve what did not work

Capture an attempted procedure, its exact version, environment, observed outcome, and reason for stopping. A failed attempt should count against a procedure only within comparable conditions. An unexecuted suggestion or a missing follow-up is not a failure.

A consultant should see: “This procedure was attempted in comparable cases but did not restore the affected workflow,” with authorized case evidence. The system must distinguish a technical failure from incorrect execution, unmet prerequisites, and unrelated changes. This is a recommendation policy, not a causal conclusion automatically inferred from ticket text.

**Demo moment:** Atlas avoids the same unsuccessful workaround already attempted by another authorized team. The benefit is less repeated troubleshooting, even when no final fix is known.

### 3.4 Evidence View — show support, gaps, and conflicts

For each important step, display its supporting source passage, source version, environment match, and verification status. Keep “source says,” “consultant observed,” and “model inferred” visibly distinct.

A conflict detector can nominate inconsistent claims for review, but a deterministic policy decides whether they may be used. Compare scope and supersession before age. A current local exception can coexist with a vendor procedure if their applicability differs. An unresolved contradiction involving a production action should lead to review, not a blended answer.

**Demo moment:** an older article is not merely ranked lower; Atlas explains that its procedure assumes a configuration absent from this incident. Users can inspect the evidence immediately.

### 3.5 Resolution Receipt — learn from confirmed work

After the consultant confirms recovery, create a draft record of what was observed, tried, changed, and validated. Suggest an update to an existing passport before creating a new one. The knowledge owner approves material procedure changes; an existing approved procedure can accumulate separately verified outcome events.

Reopening a ticket should revise outcome status rather than delete history. “No reopening observed” and “business owner confirmed successful completion” are different levels of evidence. This implements a practical feedback loop consistent with KCS’s emphasis on reuse and improvement during work. [KCS practices](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/041).

**Demo moment:** a resolved case improves the evidence available for the next similar case, while the interface shows exactly what changed and who confirmed it.

### 3.6 Recurrence Radar — turn repeated support effort into prevention

Aggregate authorized incident families and estimate where durable remediation could save the most consultant time. A recurring failure becomes a proposed problem-management investigation with its affected systems, known workarounds, evidence gaps, and responsible owner.

Rank opportunities using recurrence, measured handling effort, affected business scope, and confidence in grouping. Do not equate a temporal association with a root cause. Forecasting a future outage requires telemetry, labels, and prospective validation that historical ticket similarity alone does not supply.

**Demo moment:** after resolving one incident, the team sees a cluster of related incidents and a draft prevention proposal. Keep this to a simple trend view in the prototype; build forecasting only after enough validated history exists.

### Feature priority

| Capability | User value hypothesis | Demo impact | Complexity | Recommendation |
|---|---|---|---|---|
| Environment Lens | Avoid inapplicable procedures | High | Medium | Core prototype |
| Evidence View | Faster verification and trust | High | Medium | Core prototype |
| Next Best Question | Reduce unnecessary investigation | High | Medium with authored branches | Core prototype |
| Resolution Receipt | Reduce knowledge capture effort | High | Medium | Core prototype |
| Failure Memory | Avoid repeated failed attempts | High | Medium; labels are difficult | Small prototype example, expand in pilot |
| Recurrence Radar | Support durable problem removal | Medium | Medium to high | Lightweight demo, later pilot |
| Sandbox rehearsal | Detect some procedure failures before execution | High | High; depends on representative environment | Later, narrow procedures only |
| Autonomous remediation | Reduce manual execution | Potentially high | Very high | Defer until separately justified |

These are qualitative design judgments, not surveyed scores. A full digital twin, unrestricted self-healing, or a large collection of conversational agents would introduce substantial dependencies before establishing the core value.

## 4. Technical design

### Data flow

```text
Internal KB + historical tickets + approved SAP sources + SharePoint
        |
        v
Identity-aware source adapters and ingestion/federation policy
        |
        v
Versioning, extraction, deduplication, redaction, and source lineage
        |
        v
Searchable evidence + structured Solution Passports + outcome events
        ^
        |
Ticket context -> authorization -> hybrid retrieval -> applicability checks
        -> candidate ranking -> diagnostic branch or grounded procedure
        -> consultant review -> approved work -> observed outcome
        -> draft knowledge update -> owner review
```

Authorization applies across the entire path, including derived content, caches, source previews, and analytics. It is not just a step that runs once at sign-in.

### Source strategy

| Source | Recommended starting approach | Critical dependency |
|---|---|---|
| Historical tickets | Approved exports for demonstration; supported incremental API integration for pilot | Field-level visibility, attachments, closure quality, duplicate outages, and time of evidence availability |
| Internal knowledge base | Ingest a scoped set of approved articles with versions and ownership | Draft versus published state and inherited access restrictions |
| SharePoint | Evaluate delegated retrieval first; use controlled indexing where necessary | Tenant policy, document types, licensing, preview acceptance, and effective permissions |
| SAP Help and support content | Public documentation plus approved customer-accessible content; retain links and applicability metadata | Entitlements and permitted reuse of each source |
| SAP Notes and non-public KBAs | Supported authenticated access validated with the customer and SAP; use a deep-link handoff when needed | No assumption of a general bulk export or redistribution entitlement |
| Inventory and diagnostics | Read-only integration with selected system facts, logs, and change records | Data freshness, exact system identity, and diagnostic privileges |

SAP documentation associates access to non-public knowledge with S-user authorization. SAP also documents a Notes-search API used by ANST, but this does not establish a general-purpose ingestion contract for the proposed product. Confirm supported integration, storage, and reuse rights for the specific customer deployment. Until then, prototype using synthetic support references and permitted public content. [SAP S-user sign-in](https://help.sap.com/docs/built-in-support/user-guide-for-key-users/76582f630b354f009c4c655c6044b0b5.html), [SAP ANST documentation](https://support.sap.com/en/tools/troubleshooting.html).

### SharePoint requires an explicit architectural decision

Microsoft’s SharePoint indexer documentation describes preview ACL support and recommends considering a remote SharePoint knowledge source for custom RAG applications. The indexer also lists environmental limitations, including Conditional Access and private endpoint limitations. Consequently, it should not be assumed to fit an enterprise tenant without testing. [SharePoint indexer](https://learn.microsoft.com/en-us/azure/search/search-how-to-index-sharepoint-online).

The remote SharePoint knowledge source is documented as preview and queries via the Copilot Retrieval API on behalf of the user. Treat preview acceptance as a deployment decision. The Retrieval API documentation describes Copilot-license access and a preview consumption option for some unlicensed-user scenarios, plus retrieval limitations such as unsupported image/chart retrieval. Verify the chosen route against the actual tenant and document corpus before committing. [Remote SharePoint source](https://learn.microsoft.com/en-us/azure/search/agentic-knowledge-source-how-to-sharepoint-remote), [Retrieval API overview](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/overview).

For indexed content, current ACL documentation distinguishes automatically refreshed item-level changes from inherited parent-scope changes requiring an explicit refresh. It also documents unsupported group relationships. Every chunk needs the correct permissions, and revocation must invalidate derived results. If authorization cannot be established, withhold the content. A dedicated permission test corpus is a release requirement. [SharePoint ACL ingestion and synchronization](https://learn.microsoft.com/en-us/azure/search/search-indexer-sharepoint-access-control-lists).

### Retrieval and ranking

Use exact lexical matching for error codes, transaction identifiers, and component names alongside semantic retrieval for narrative symptoms. Fuse candidate lists and rerank the authorized results. Azure AI Search documents reciprocal rank fusion for combining retrieval rankings; this is a reasonable managed option for a Microsoft-oriented deployment. [Hybrid search ranking](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking).

Recommended sequence:

1. Establish tenant, client, user identity, and allowed source scope on the server.
2. Normalize incident facts while preserving exact technical identifiers and uncertainty.
3. Retrieve only authorized evidence; apply hard environment exclusions where metadata is reliable.
4. Deduplicate candidates and preserve independent evidence counts.
5. Assess environment compatibility, prerequisite completeness, current source validity, and observed outcomes.
6. Rank eligible procedures; ask a question when its answer can change the preferred action.
7. Generate a structured recommendation from the selected evidence.
8. Validate source references, required fields, unsupported steps, and action policy before display.

The early ranking can be an explicit, inspectable heuristic: relevance plus compatibility, evidence quality, and comparable outcomes, minus unresolved conflicts and operational cost. Calibrate weights on held-out incidents rather than presenting arbitrary coefficients as research findings. Hard policy failures must never be canceled out by a high similarity score.

Once sufficient outcome data exists, estimate success conditional on the environment and prerequisites, with shrinkage for small samples. Raw success rates are biased by case difficulty and consultant selection. Retrieval scores, a model’s verbal confidence, and an outcome probability are different quantities. In the prototype, display evidence labels and sample counts; do not fabricate “97% confidence.”

### Why a graph is optional at first

Explicit relationships are useful: a procedure applies to a release, supersedes another procedure, requires a configuration, and was attempted in an incident. A relational schema with link tables can represent these relationships initially. Add a graph database only when measured query needs justify it.

Microsoft’s GraphRAG work targets complex discovery and global questions, and explicitly discusses graph-index construction cost. That makes it a candidate for later cross-incident synthesis, not an automatic prerequisite for retrieving a known fix. Compare it against the simpler baseline on representative tasks. [Microsoft GraphRAG discussion](https://www.microsoft.com/en-us/research/blog/graphrag-new-tool-for-complex-data-discovery-now-on-github/).

### Stack recommendation and alternatives

For a Microsoft-heavy customer, a sensible candidate stack is a web or ITSM-native panel, a typed API service, Azure AI Search, a relational store for passports and outcomes, enterprise identity, object storage for permitted artifacts, and an approved model endpoint. Use a queue for ingestion and an explicit workflow state machine for investigation. Benchmark the model on the support dataset before selecting one.

For an SAP-centered platform team, SAP HANA Cloud is a candidate for vector and structured storage; official documentation supports vector indexing. This is an alternative implementation route, not a reason to add a second vector database. Select based on existing operations, data placement, and total integration effort. [SAP HANA Cloud vector index documentation](https://help.sap.com/docs/HANA_CLOUD_DATABASE/c40cab369db246f1a17feea1c031ddc1/ab672646e17c46e8ab60463efa22558d.html).

Keep the model replaceable. The durable product assets are the evaluated passport schema, labeled applicability cases, source lineage, and verified outcomes. Initial “learning” means updating those stores and evaluated ranking rules; it does not require continuously retraining a foundation model on customer incidents.

## 5. Trust, operations, and knowledge maintenance

Retrieved tickets and documents are untrusted input. They may contain misleading instructions, secrets, or malicious text. OWASP identifies prompt injection as a threat that RAG does not remove. Use constrained tool interfaces, independent authorization, and separation between evidence text and executable actions. A model-based reviewer is an additional check, not an authorization boundary. [OWASP prompt injection guidance](https://genai.owasp.org/llmrisk/llm01-prompt-injection/).

Recommended product controls are directly tied to support risks:

| Risk | Required implementation behavior |
|---|---|
| Cross-client disclosure | Enforce client isolation independently of prompts. Propagate access restrictions to summaries, embeddings, previews, logs, and metrics. |
| Permission revoked after ingestion | Revalidate sensitive results, invalidate caches, and fail closed when policy state is stale or unavailable. |
| Unsupported operational action | Produce a diagnostic or escalation response when a procedure lacks evidence or prerequisites. |
| Malicious source instructions | Treat source text only as evidence; no arbitrary commands, external destinations, or tool calls from document content. |
| Inaccurate knowledge update | Version drafts, require accountable review, and preserve provenance and rollback history. |
| Weak feedback | Distinguish clicked, accepted, attempted, confirmed, failed, reopened, and unknown. |
| Source outage | Show partial-source coverage and timing; never present a partial search as comprehensive. |
| Stale environment facts | Show collection time and request reconfirmation before relying on a material fact. |

For the initial pilot, keep production-changing actions outside the assistant. Later automation should execute only approved, versioned procedures through an independent gateway that validates actor, target, parameters, preconditions, and change authorization. A successful sandbox check cannot guarantee production safety because data, topology, load, and permissions can differ.

Assign an operational owner for every source adapter and a domain owner for every promoted procedure. Establish a queue for contradictions, repeated failures, broken citations, and obsolete articles. KCS’s Evolve Loop provides an established model for using aggregate support activity to improve knowledge and processes. [KCS Evolve Loop](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040).

## 6. Prototype and pilot roadmap

### Demonstrator: approximately 2–3 weeks

Assume two engineers, a part-time designer, and an available SAP/support specialist; elapsed time depends on access and experience. Use synthetic data to avoid waiting for production connectors. Implement three incident stories and four labeled source types, with transparent fixture data.

The minimum convincing scope is a working evidence retrieval path, rule-based applicability checks, one diagnostic decision branch, source previews, and a local feedback update. Generated explanations may use a real model if an approved endpoint is available; otherwise use explicitly labeled scripted text. A simulated connector must never appear “live.” See the companion blueprint for interaction states and acceptance criteria.

### Scoped pilot: approximately 8–12 weeks after access is approved

| Stage | Deliverable | Gate |
|---|---|---|
| Weeks 1–2 | Baseline, source inventory, permission model, reviewed incident sample | One usable domain and agreed outcome definitions |
| Weeks 3–4 | One ticket integration and scoped KB/SharePoint route | Permission and revocation tests pass |
| Weeks 5–6 | Retrieval, passports, applicability checks, offline benchmark | Better than keyword and basic RAG baselines on agreed metrics |
| Weeks 7–8 | Shadow mode and consultant usability sessions | No critical policy failures; unsupported outputs understood |
| Weeks 9–12 | Controlled live assistance and knowledge maintenance workflow | Useful time savings with no unacceptable quality degradation |

SAP content integration is a separate dependency: if access remains unresolved, limit the pilot to approved internal material and authenticated links. Do not expand production scope just to meet a calendar estimate.

### Later expansion

Add more application families, tenant-safe reuse of separately approved generalized procedures, deeper read-only diagnostics, and recurrence analysis. Cross-client knowledge pooling requires an explicit governance design; removing names alone does not establish that a procedure or incident history is safe to share. Automated changes and predictive outage prevention need separate evaluations and operating agreements.

## 7. Evaluation that can establish real value

### Build a benchmark that cannot see the future

Start with approximately 200–400 expert-reviewed historical cases as an initial engineering benchmark, expanding based on category coverage and uncertainty. Include answerable cases, ambiguous cases, missing knowledge, failed fixes, obsolete procedures, and permission-boundary cases. Two domain reviewers should label applicable solutions and useful next actions; adjudicate disagreements.

Replay each ticket at its original arrival time. The input must exclude its eventual resolution, later work notes, and documents created after that time. Keep duplicated tickets and shared-outage clusters together when splitting data. A separate set should test unfamiliar incident families. Evaluate both time-consistent retrieval and whether the final action was supported.

Compare four systems: keyword search, semantic search, basic cited RAG, and Atlas with applicability and diagnostic logic. If the customer already owns a relevant assistant, include it in a tenant-approved comparison. Run ablations that remove applicability checks or outcome history to establish whether the differentiators add value.

AIOpsLab supplies an example of reproducible evaluation across operational tasks and environments. Use that evaluation philosophy; its cloud microservice tasks do not validate SAP procedures. [AIOpsLab project](https://microsoft.github.io/AIOpsLab/).

### Proposed gates, not results

| Metric | Definition | Initial planning gate |
|---|---|---|
| Top-3 applicability | Answerable cases with at least one expert-approved applicable candidate in top three | At least 85%, reported by category and sample count |
| Citation validity | Checked citations that exist and support the associated material claim | At least 95%; critical action support separately reviewed |
| Unsafe advice | Advice violating known hard prerequisites or action policy | Zero observed critical cases in the defined release suite |
| Permission isolation | Unauthorized content exposed in defined retrieval, preview, cache, and derived-output tests | Zero observed leaks; a failure blocks release |
| Abstention quality | Appropriate escalation on unsupported cases, balanced against unnecessary abstention | Report precision, recall, and answer coverage; set threshold after baseline |
| Time to useful recommendation | Time from opening a case to an expert-judged useful action | Target a 25% median reduction in a controlled pilot |
| Interactive latency | Time to a grounded initial recommendation | Initial p95 target below 10 seconds under agreed load |
| Resolution quality | Reopening, failed procedure attempts, and audited correctness | Pre-agreed non-inferiority margin relative to baseline |

Zero observed failures does not mean zero underlying risk. Report denominators, confidence intervals where appropriate, severity, and test coverage. A 200-case benchmark is not sufficient evidence for unrestricted production automation.

For the live pilot, allocate comparable teams or shifts with attention to knowledge spillover and incident mix. Prefer randomized assignment where practical; otherwise use a matched design and disclose residual confounding. Separate novice and experienced consultants, incidents and requests, and severe outages from routine tickets. Track active consultant effort separately from wall-clock resolution time, which includes waiting for users, change windows, or vendors.

### Economic model

The following is an illustrative capacity calculation, not a price quote or forecast:

```text
Monthly incidents                         10,000
Share within supported scope                 40%
Consultant adoption on those incidents        60%
Average active minutes saved per use            8

Monthly gross hours released
  = 10,000 × 0.40 × 0.60 × 8 ÷ 60
  = 320 hours
```

At an assumed internal loaded cost of RM120/hour, that is RM38,400/month of gross capacity value. Holding the other assumptions constant, 4 minutes saved produces 160 hours and RM19,200; 12 minutes produces 480 hours and RM57,600. The currency and rate are illustrative and should be replaced by the organization’s figures.

Subtract model usage, search/storage, connector licensing, operations, knowledge review, incremental verification, and amortized implementation effort. Released time becomes cash savings only if expenditure actually changes; otherwise it is capacity for backlog reduction or service improvement. Do not add resolution-time savings to the same underlying handling-time savings a second time. Downtime avoidance belongs in a separate, evidence-based business-impact model.

## 8. Build-versus-buy decision

Run a short capability bake-off before committing to a custom platform. Use the same incident sample, permissions, and source coverage for the native ITSM assistant, an enterprise-search option, and the proposed Atlas layer. Evaluate environment applicability, failure-memory usefulness, source access, effort to maintain integrations, and total ownership cost.

If existing tools provide sufficient value, build the passport, applicability, and outcome layer as an extension. If they cannot enforce the necessary customer boundaries or support the specialized evidence workflow, implement a separate orchestration service and integrate its panel into the current support tool. The recommended default is to reuse existing search and identity infrastructure while owning the domain-specific decision logic.

The durable advantage is accumulated, trustworthy resolution evidence and the ability to apply it correctly. A chatbot interface, a vector database, or an agent framework by itself is unlikely to provide that advantage.

## 9. Questions to resolve before implementation

The critical discovery work is operational: identify the ticketing platform and licenses, the first application family, the real recurrence rate, the quality of resolution records, and the locations where consultants currently find answers. Review 30–50 cases with consultants rather than relying only on management estimates.

Then establish whether this is one enterprise or a managed-service provider serving multiple clients; how client boundaries map to identity; which SAP sources may be accessed and retained; which SharePoint permission structures and document formats are in scope; and whether approved model endpoints and telemetry are available.

Finally, name the people who can validate a solution, approve a knowledge change, and own a failed recommendation. Without those roles, an ingestion pipeline can accumulate content but cannot establish the best-known solution.

## Sources

Publication dates are given where reliably available. Undated product pages are living documentation accessed September 15, 2026. Public documentation establishes the stated capabilities; it does not establish tenant eligibility, commercial terms, or performance in this project.

1. ServiceNow. [Investigate and resolve ITSM incidents](https://www.servicenow.com/docs/r/xanadu/it-service-management/now-assist-for-it-service-management-itsm/now-assist-itsm-aiagents-incident-resolver-workflow.html). Xanadu documentation, updated March 28, 2025. Incident recommendations baseline.
2. ServiceNow. [Generating AI summary and next steps](https://www.servicenow.com/docs/r/it-service-management/generating-ai-native-itsm.html). Australia documentation, updated March 12, 2026. Current incident experience.
3. SAP. [Knowledge Tab](https://support.sap.com/content/s4m/help/support/search.html). Living documentation. Unified search and generated answers.
4. SAP. [Troubleshooting Tools](https://support.sap.com/en/tools/troubleshooting.html). Living documentation. Support Log Assistant, ANST, PANKS, and Note Assistant.
5. SAP. [Signing In with Your S-user ID](https://help.sap.com/docs/built-in-support/user-guide-for-key-users/76582f630b354f009c4c655c6044b0b5.html). Living documentation. Non-public knowledge access.
6. Atlassian. [AI answers in the virtual service agent](https://support.atlassian.com/jira-service-management-cloud/docs/atlassian-intelligence-answers-in-the-virtual-agent/). Living documentation. Knowledge-based self-service.
7. Glean. [Configure Glean in ServiceNow](https://docs.glean.com/administration/platform/embedded-integrations/glean-in-service-now). Living documentation. Support capabilities and integration migration notice.
8. Consortium for Service Innovation. [KCS v6 Practices Guide: Summary](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/041). Living guide. Workflow-based knowledge capture and reuse.
9. Consortium for Service Innovation. [The Evolve Loop](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040). Living guide. Organizational learning and content health.
10. Brynjolfsson, E., Li, D., and Raymond, L. [Generative AI at Work](https://arxiv.org/abs/2304.11771v2). Revised November 6, 2024. Empirical support productivity evidence and heterogeneous effects. The revised figures are used instead of the earlier 14%/5,179-agent version.
11. Lewis, P., et al. [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401). 2020. Retrieval-generation foundation.
12. Roy, D., et al. [Exploring LLM-based Agents for Root Cause Analysis](https://www.microsoft.com/en-us/research/publication/exploring-llm-based-agents-for-root-cause-analysis/). FSE 2024. Diagnostic retrieval and evaluation evidence.
13. Microsoft. [AIOpsLab](https://microsoft.github.io/AIOpsLab/). Project site; initial research announced in 2024. Operational-agent evaluation approach.
14. Microsoft. [Hybrid search ranking](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking). Living documentation. Reciprocal rank fusion.
15. Microsoft. [SharePoint in Microsoft 365 indexer](https://learn.microsoft.com/en-us/azure/search/search-how-to-index-sharepoint-online). Living documentation. Ingestion approaches and limitations.
16. Microsoft. [SharePoint ACL ingestion](https://learn.microsoft.com/en-us/azure/search/search-indexer-sharepoint-access-control-lists). Updated August 12, 2026. Permission support, inheritance, and synchronization limitations.
17. Microsoft. [Remote SharePoint knowledge source](https://learn.microsoft.com/en-us/azure/search/agentic-knowledge-source-how-to-sharepoint-remote). Living preview documentation. Federated retrieval option.
18. Microsoft. [Microsoft 365 Copilot Retrieval API overview](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/overview). Updated August 20, 2026. Retrieval capabilities, licensing routes, and limitations.
19. Microsoft Research. [GraphRAG: New tool for complex data discovery now on GitHub](https://www.microsoft.com/en-us/research/blog/graphrag-new-tool-for-complex-data-discovery-now-on-github/). 2024. Graph retrieval suitability and indexing tradeoffs.
20. SAP. [CREATE VECTOR INDEX](https://help.sap.com/docs/HANA_CLOUD_DATABASE/c40cab369db246f1a17feea1c031ddc1/ab672646e17c46e8ab60463efa22558d.html). SAP HANA Cloud Vector Engine Guide, QRC 2/2026. SAP-centered storage alternative.
21. OWASP. [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/). 2025 risk guidance. Retrieved-content and tool-boundary risks.
