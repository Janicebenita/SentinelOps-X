# Pub/Sub eventing

Status: `IMPLEMENTED_REQUIRES_CREDENTIALS`

Pub/Sub is the planned managed asynchronous backbone for agent tasks,
scenarios, verification, model invocations, evidence exports, BigQuery exports,
and workflow events. Provisioning creates the named topics, worker
subscriptions, and dead-letter topics idempotently. Messages include a schema
version, event ID, correlation ID, trace ID, and the explicit no-production
boundary. `schemas/pubsub/event-envelope-v1.avsc` is the managed Avro schema
bound to newly provisioned primary topics with JSON message encoding.

The backend workflow remains authoritative. Consumers must validate schema and
idempotency before processing; poison messages are routed through dead-letter
policy in the managed configuration. A message cannot approve, alter a
mandatory gate, or invoke production infrastructure.

Authenticated proof:

```powershell
$env:PROJECT_ID='sentinelops-nexus-finale'
python scripts/provision_pubsub.py
python scripts/smoke_pubsub.py
```

The smoke output records topic, subscription, publish message ID, event ID,
correlation ID, and trace ID. Managed publish/consume is not marked verified
until these values come from the target project.

`PRODUCTION ACTION: NOT EXECUTED`
