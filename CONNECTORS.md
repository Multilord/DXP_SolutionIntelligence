# Source connectors

Source synchronization is read-only against upstream systems. Sync runs explicitly from Knowledge sources, one page per request. It stores evidence, not automatically approved procedures. Build the semantic index after sync. Application user authentication remains excluded; source service credentials are still required.

## SharePoint Online

Set `SHAREPOINT_TENANT_ID`, `SHAREPOINT_CLIENT_ID`, `SHAREPOINT_CLIENT_SECRET` and `SHAREPOINT_DRIVE_ID`. An administrator must grant the application read access to the intended document library through Microsoft Graph. The adapter uses the client-credentials flow and `/drives/{drive-id}/root/delta`; it does not grant itself access.

The adapter persists a continuation/delta token, imports supported text/PDF/DOCX files, versions changes and retracts deleted files. Click Sync next page until complete; later syncs read changes since the last token. Downloads are bounded at 4 MiB and supported only from SharePoint Online `.sharepoint.com` hosts. The bearer token is never forwarded to signed download URLs. Failed pages retain the earlier cursor for retry. Token expiry/reset recovery requires an administrator to reset connector state; automatic full rescan and permission synchronization are not implemented. Use a dedicated library for prototype data.

## Internal KB, tickets and SAP exports

Configure the applicable HTTPS URL and optional bearer token:

| Source | URL | Token |
|---|---|---|
| Internal KB | `KB_FEED_URL` | `KB_FEED_TOKEN` |
| Resolved tickets | `TICKET_FEED_URL` | `TICKET_FEED_TOKEN` |
| Authorized SAP repository export | `SAP_FEED_URL` | `SAP_FEED_TOKEN` |

These are normalized JSON feed adapters. They do not claim universal compatibility with SAP Notes, ServiceNow, Jira or arbitrary KB APIs. An organization-specific export or mapping layer must expose this schema:

```json
{
  "records": [
    {
      "id": "KB-123",
      "title": "Approved support handover structure",
      "content": "Include the incident summary, affected system version, observed symptoms, attempted actions and verification evidence.",
      "url": "https://knowledge.example/articles/KB-123"
    },
    {"id": "KB-OLD", "deleted": true}
  ]
}
```

At most 50 records per response, 100,000 text characters per record and 4 MiB per response. Omitted records are not treated as deletions; send explicit tombstones. IDs are stable within a connector. Changed content increments the stored version and requires new embeddings. Old procedure links are removed on source change. A linked reviewed procedure remains a separate record and cannot use withdrawn evidence for retrieval.

## Verification boundaries

Automated tests exercise idempotent import, version updates, deletion, invalid payloads and safe status responses. SharePoint's live tenant permissions and all actual organizational feeds require real integration testing. No external source credentials are included in the repository, and connector status never returns tokens or signed URLs.

Reference: [Microsoft Graph drive delta](https://learn.microsoft.com/en-us/graph/api/driveitem-delta?view=graph-rest-1.0).
