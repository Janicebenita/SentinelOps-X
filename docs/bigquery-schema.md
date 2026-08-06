# BigQuery analytical schema

Status: `IMPLEMENTED_REQUIRES_CREDENTIALS`

The `sentinelops_nexus` dataset is analytical storage; SQLite remains the
authoritative transactional workflow store. Nine idempotent DDL files under
`sql/bigquery/` define telemetry, workflow, agent, model, scenario,
verification, business-impact, audit-export, and forecast-evaluation tables.

Every table is ingestion-time queryable, partitioned by
`DATE(event_timestamp)`. The dedicated audit export is clustered by
`workflow_id`, `event_type`, and `actor_type`; it carries actor attribution,
trace and correlation IDs, JSON payload, payload hash, previous hash, chain
position, signer metadata, evidence IDs, and schema version.

Retention should be configured through a dataset/table expiration policy in
the target project (recommended: 400 days for the demonstration dataset).
Writers must redact credentials, raw tokens, secrets, and sensitive payloads.
`event_id` is the idempotency key and must be deduplicated before retries.

Provision and run the authenticated write/read proof:

```powershell
$env:PROJECT_ID='sentinelops-nexus-finale'
python scripts/provision_bigquery.py
python scripts/smoke_bigquery.py
```

The smoke test inserts a non-secret audit row, reads it back, and prints the
row ID, query job ID, and SHA-256 payload hash. No successful Cloud evidence is
claimed until those identifiers are captured from an authenticated run.

`PRODUCTION ACTION: NOT EXECUTED`
