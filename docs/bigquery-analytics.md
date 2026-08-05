# BigQuery Analytics

`sql/bigquery_schemas.sql` defines partitioned, clustered tables for telemetry, workflows, agents, scenarios, verification, models, impact, audit copies and forecast evaluation. Stable insert IDs support idempotency. Cloud writes require credentials and should batch with retry/redaction; local SQLite remains the deterministic fallback, not Cloud Run durability.
