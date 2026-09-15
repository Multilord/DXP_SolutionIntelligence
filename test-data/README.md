# Solution Atlas manual test pack

These fixtures are synthetic and safe to use in the local demonstration. Start the app with `python -m backend.run`, then open <http://127.0.0.1:8000>.

## Test 1 — existing solution with a diagnostic branch

Create a new incident with:

| Field | Value |
|---|---|
| Title | Invoice approval fails only from the primary screen |
| System | Finance applications |
| Error identifier | APPROVAL_TIMEOUT |
| Description | After the DEMO-R2 deployment, invoice approval hangs on the primary screen with APPROVAL_TIMEOUT. Other finance applications remain available and no configuration change has been attempted. |

Analyze it. Atlas should find the approval-route precedents and ask whether the alternate application path works.

- Choose **Yes, it works** to receive the reviewed route runbook.
- Create the incident again and choose **No, it also fails** to see the route-only fix withheld.
- Choose **Not sure** to keep investigation open without inventing an answer.

## Test 2 — direct guided runbook and failed-attempt memory

Create a new incident with:

| Field | Value |
|---|---|
| Title | Nightly integration batch waiting at downstream handoff |
| System | Operations integrations |
| Error identifier | QUEUE_WAIT |
| Description | The nightly integration batch remains pending at the downstream handoff with QUEUE_WAIT. A service restart was attempted once and did not restore processing. |

Expected result: **Inspect the downstream queue dependency** appears as a guided runbook. The original seeded incident SYN-1043 also demonstrates the stored failed restart.

## Test 3 — quick-reference answer

Create a new incident with:

| Field | Value |
|---|---|
| Title | Need the approved incident handover template |
| System | Operations integrations |
| Error identifier | Leave blank |
| Description | I need the approved support handover template and the evidence fields required before passing an incident to another consultant. |

Expected result: a compact **Quick reference** response instead of a troubleshooting runbook.

## Test 4 — no precedent and knowledge capture

Create a new incident with:

| Field | Value |
|---|---|
| Title | Payment export creates a cobalt manifest signature |
| System | Operations integrations |
| Error identifier | COBALT_MANIFEST_42 |
| Description | The new payment export completes but creates the unexpected signature COBALT_MANIFEST_42. No existing support procedure explains the signature or its validation requirements. |

Analyze it. Expected result: **Investigation needed** and a knowledge gap.

Use **Capture verified resolution** with:

| Field | Value |
|---|---|
| Reusable solution title | Validate the cobalt export manifest fixture |
| Actions taken | Compare the generated manifest with the approved test fixture.\nConfirm the exporter is using the current fixture revision.\nHave the integration owner correct the confirmed fixture mapping.\nRepeat the export and retain the resulting checksum. |
| Recovery verification | Repeated the synthetic export twice and confirmed that both manifests matched the approved fixture checksum. |

Enter each action on a separate line. After indexing completes, open **Review queue**, inspect the source, approve it, then analyze the incident again. The new runbook should now be returned.

## Test 5 — staleness after a system change

First analyze the seeded incident **SYN-1043**. Then open **System timeline** and record:

| Field | Value |
|---|---|
| Affected system | Operations integrations |
| Change description | Downstream queue routing policy updated for the September release |
| Procedure impact | Unknown — requires revalidation |

Analyze SYN-1043 again. Expected result: the previously supported procedure now needs revalidation.

Open **Solution library**, locate **Inspect the downstream queue dependency**, and record this verification:

> Compared the procedure with the current queue policy and observed one complete synthetic batch through the downstream handoff.

Analyze the incident again. The runbook should be supported for the new system revision.

## Test 6 — known incompatibility

Record another mock change:

| Field | Value |
|---|---|
| Affected system | Operations integrations |
| Change description | Legacy queue inspection procedure removed by protocol migration |
| Procedure impact | Known incompatible — blocks procedure |

Expected result: the old procedure is marked **Not applicable**. Trying to revalidate it should be rejected because verification cannot override a known incompatibility.

This permanently changes the current local demo state. Use it near the end of your testing or start a fresh data directory first.

## Test 7 — record outcomes

On a supported runbook, use these examples:

**Confirmed recovery**

> Completed every reviewed step and observed two successful synthetic batches after the downstream dependency recovered.

**Attempted — did not resolve**

> The dependency check completed, but the batch remained in QUEUE_WAIT and no successful handoff was observed.

**Still unverified**

> The procedure was reviewed, but the maintenance window ended before a complete batch could be observed.

## Test 8 — source ingestion

Open **Knowledge sources** and upload the files in this folder:

1. `queue-operations-note.md` — valid Markdown and relevant evidence.
2. `approval-observations.csv` — valid CSV.
3. `export-reference.json` — valid JSON.
4. `malformed-example.json` — deliberately invalid JSON; its job should fail visibly.

Upload `queue-operations-note.md` twice with the same source type. The second upload should be detected as a duplicate.

Uploaded files can appear as supporting evidence but cannot become approved runbooks automatically.

## Test 9 — input validation

Try these intentionally invalid values:

- Incident title: `Bug` — too short.
- Incident description: `It failed.` — too short.
- Capture step: `Fix` — too short.
- Verification: `Works now` — too short.
- Unsupported upload: rename a disposable text file to `.exe` — rejected before ingestion.

The form or API should display a useful error and preserve the existing workspace data.

## Fresh test workspace

To preserve the current demo and start with clean seed data, stop the server and run:

```powershell
$env:ATLAS_DATA_DIR = Join-Path $env:LOCALAPPDATA 'SolutionAtlas\manual-test'
python -m backend.run
```

Use a different final folder name for another independent test run.
