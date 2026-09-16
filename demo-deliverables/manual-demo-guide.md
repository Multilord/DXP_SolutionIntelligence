# Solution Atlas: manual demo and narration

Target: 1 minute 50 seconds, recorded in separate clips. Use http://127.0.0.1:8000/ for the newly added logo. Keep the backend terminal running. Recording and narration have not been produced by this guide.

## Before recording

- Maximize the browser, use readable zoom, and hide notifications and unrelated tabs.
- Confirm Connected and 7/7 sections embedded. Keep the Atlas temporary rule active.
- Record the approval result before experimenting with captures or system changes: those can invalidate cached answers.
- Current SYN-1042 goes directly to a guided runbook. Do not look for a diagnostic question. If it later asks about the alternate path, answer Yes only as the declared synthetic scenario observation.
- Record silent clips first, then voice-over. Trim long loading intervals with a “Processing time shortened” caption. Never replace an API error with a staged successful response.
- During inspection, approval analysis/evidence/alternatives worked. Subsequent checksum analysis hit provider quota errors; the final attempt produced no usable result. The main sequence below shows the knowledge-gap workflow as a capability explanation, not a completed capture demonstration.

## 110-second sequence

### 1. Workspace — 0:00–0:12
Click Incident workspace, scroll to the top and show the logo and hero. Add caption “Prototype · Synthetic support scenarios.”

Say: “Support teams often solve the same problems repeatedly because previous answers are scattered. Solution Atlas brings that knowledge into one workspace. This prototype uses synthetic support scenarios.”

### 2. Incident — 0:12–0:24
Press Ctrl+K, type SYN-1042, press Enter. Scroll to Invoice approval times out after deployment. Point at APPROVAL_TIMEOUT, DEMO-R2 and Hub. Click Analyze incident (or Analyze again).

Say: “Here, invoice approval hangs after a deployment. I select the incident, check its error identifier and system context, then ask Atlas to find relevant guidance.”

### 3. Runbook — 0:24–0:42
After analysis succeeds, scroll to Resolution guidance. Show Check the approval application route, Guided runbook, Context supported, matching signals, numbered steps and Verify the outcome. Do not record a successful outcome that you have not observed.

Say: “Gemini helps retrieve relevant evidence and explain the recommendation. Atlas presents a reviewed runbook, supported by matching symptoms and system context. The consultant gets ordered steps and a validation check, while remaining responsible for applying the procedure.”

### 4. Evidence — 0:42–0:56
Under Supporting evidence, click DEMO-R2 approval route guide. Hold the Source evidence drawer on screen; show DOC-101, version and exact stored source text. Click Close evidence.

Say: “The recommendation is traceable. I can open its supporting document, inspect the original passage, and see the source version. Consultants can check the evidence behind the explanation.”

### 5. Applicability — 0:56–1:12
Scroll to Alternative solutions. Expand Review the legacy approval timeout workaround. Point to Needs revalidation and the route-policy warning. Then expand Embedded deployment approval repair and show Not applicable. Do not click Record mock revalidation.

Say: “Similar solutions are not automatically suitable. This older workaround needs revalidation because it predates a recorded system change. Another fix is marked not applicable because its deployment requirements do not match.”

### 6. Timeline — 1:12–1:22
Click System timeline and show DEMO-R2 route-policy update in Applied change history. Do not record a new change during this demo.

Say: “The system timeline makes that context visible. Atlas checks recorded changes so consultants can judge whether an earlier resolution still fits.”

### 7. Knowledge loop — 1:22–1:40
Click Knowledge gaps. Hold on the Investigate → Capture resolution → Index locally → Review & publish → Reuse strip. Then click Review queue and show its review guidance. An empty queue is acceptable for this explanation; do not claim a resolution was submitted.

Say: “For issues without a usable precedent, the knowledge-gap workflow provides a path to capture what a consultant learns. New resolutions go through indexing and review before becoming reusable guidance. This is knowledge growth through a human review process.”

### 8. Closing — 1:40–1:50
Click Incident workspace and scroll to the logo and hero. Hold the last frame for two seconds.

Say: “The goal is less repeated troubleshooting and better reuse of team knowledge. Solution Atlas: find the evidence, check the context, and preserve the resolution.”

The spoken script is approximately 230–250 words. Aim for 135–145 words per minute, allowing short pauses. The timestamps describe the edited recording, not guaranteed API response time.

## Optional stronger clip 7, only after a successful checksum rehearsal

1. After recording the approval clips, select SYN-1044 and click Analyze incident.
2. Continue only if an actual Investigation needed result appears. A quota error is not a knowledge gap.
3. Click Capture verified resolution, or Knowledge gaps → Capture resolution on its card.
4. Show the fields Reusable solution title, Actions taken — one step per line, and How was recovery verified?
5. To demonstrate saving, use clearly labelled synthetic example content and record it as a simulated consultant resolution, not a real repair:
   - Title: Synthetic demo: validate the export checksum fixture
   - Actions, one per line: “Compare the mock export against the approved test fixture.” / “Have the demo owner correct the intentionally mismatched fixture configuration.” / “Repeat the mock export and compare the generated checksum.”
   - Verification: “Simulated demonstration only: the corrected mock fixture produces the expected checksum on a repeated export. No real SAP system was changed.”
6. Click Capture & index. Wait for the draft to appear in Review queue as awaiting review. Record these steps as a separate clip and shorten typing/loading during editing.
7. End with the draft awaiting review. Publication and semantic reindexing are additional operations; do not claim the draft is already available to normal AI retrieval.

Alternate narration for clip 7: “For this unfamiliar checksum issue, Atlas finds no usable precedent. After a simulated investigation, I capture the resolution and its validation notes. It enters the review queue as a draft, preserving the new knowledge for review before reuse.”

If quota errors persist, use the main workflow-explanation clip. Do not repeatedly click Analyze or promise that a fixed wait will reset the quota. Uploads, connector setup, outcome recording and publication are intentionally omitted from the 110-second recording so the central story remains readable.
