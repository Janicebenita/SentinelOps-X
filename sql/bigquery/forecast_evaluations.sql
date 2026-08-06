CREATE TABLE IF NOT EXISTS `${PROJECT}.${DATASET}.forecast_evaluations`
(event_id STRING NOT NULL, workflow_id STRING NOT NULL, event_type STRING NOT NULL,
 event_timestamp TIMESTAMP NOT NULL, actor STRING, role STRING, source_service STRING,
 target_service STRING, trace_id STRING, correlation_id STRING, payload JSON,
 payload_hash STRING, previous_hash STRING, created_at TIMESTAMP NOT NULL)
PARTITION BY DATE(event_timestamp) CLUSTER BY workflow_id, event_type, source_service;
