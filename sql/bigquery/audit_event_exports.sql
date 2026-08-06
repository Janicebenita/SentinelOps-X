CREATE TABLE IF NOT EXISTS `${PROJECT}.${DATASET}.audit_event_exports`
(
  event_timestamp TIMESTAMP NOT NULL,
  event_id STRING NOT NULL,
  workflow_id STRING NOT NULL,
  actor_type STRING,
  actor_id STRING,
  event_type STRING NOT NULL,
  payload_json JSON,
  payload_hash STRING NOT NULL,
  previous_hash STRING,
  chain_position INT64 NOT NULL,
  signature STRING,
  signer_key_id STRING,
  trace_id STRING,
  correlation_id STRING,
  evidence_ids ARRAY<STRING>,
  schema_version STRING NOT NULL,
  ingestion_timestamp TIMESTAMP NOT NULL
)
PARTITION BY DATE(event_timestamp)
CLUSTER BY workflow_id, event_type, actor_type;
