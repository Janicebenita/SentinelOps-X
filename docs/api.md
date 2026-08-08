# SentinelOps Nexus API

The predictive workflow is versioned under `/api/v1`. The older `/api` incident-repair endpoints remain available as a secondary compatibility path.

## Health

- `GET /api/v1/health`
- `GET /api/v1/readiness`

Both responses explicitly report `production_action: NOT EXECUTED`.

## Deterministic demo

- `POST /api/v1/demo/reset`
- `POST /api/v1/demo/seed`
- `GET /api/v1/demo/status`
- `GET /api/v1/telemetry?run_id={id}`

## Workflow

- `POST /api/v1/workflows`
- `GET /api/v1/workflows`
- `GET /api/v1/workflows/{id}`
- `POST /api/v1/workflows/{id}/observe`
- `POST /api/v1/workflows/{id}/predict`
- `POST /api/v1/workflows/{id}/build-twin`
- `POST /api/v1/workflows/{id}/simulate`
- `POST /api/v1/workflows/{id}/tournament`
- `POST /api/v1/workflows/{id}/verify`
- `POST /api/v1/workflows/{id}/business-impact`
- `POST /api/v1/workflows/{id}/recommend`
- `POST /api/v1/workflows/{id}/run-all`
- `POST /api/v1/workflows/import-json`

Invalid state transitions return HTTP `409` with the expected state. Model/provider outputs never directly change workflow state.

### Operational JSON import

`POST /api/v1/workflows/import-json` accepts a JSON filename and its JSON content. The backend—not the browser—normalizes the document, creates a new workflow, persists the uploaded source and its SHA-256 hash, calculates the forecast, and replays the 12 deterministic scenarios.

Two input forms are supported:

- a `controls` object containing `traffic_multiplier`, `redis_capacity`, `application_replicas`, and `dependency_latency_ms`;
- at least three telemetry rows under `telemetry`, `telemetry_points`, `observations`, `points`, `metrics`, `records`, `samples`, `series`, or `data`, with time/minute, request rate, Redis memory percentage, Redis CPU percentage, p50/p95/p99 latency, cache-hit percentage, queue depth, application replicas, and error-rate values. Finite numeric values may be JSON numbers or numeric strings. `redis_capacity` must be supplied in the configuration or latest telemetry point because it cannot be inferred safely from percentages alone.

Common field aliases are normalized. Missing operational metrics return HTTP `409` with a precise explanation; the service does not invent telemetry or present an incident/status document as a calculated prediction. Every successful import retains `PRODUCTION ACTION: NOT EXECUTED`.

## Human decision

- `POST /api/v1/workflows/{id}/approve`
- `POST /api/v1/workflows/{id}/reject`
- `POST /api/v1/workflows/{id}/request-evidence`

Each endpoint requires a matching typed decision, named actor and rationale. Approval records a decision and enables evidence export only.

## Evidence and audit

- `GET /api/v1/workflows/{id}/evidence`
- `POST /api/v1/workflows/{id}/evidence/upload`
- `GET /api/v1/workflows/{id}/agents`
- `GET /api/v1/workflows/{id}/timeline`
- `GET /api/v1/workflows/{id}/events` (SSE snapshot)
- `GET /api/v1/workflows/{id}/export`
- `GET /api/v1/audit/verify?run_id={id}`

Interactive OpenAPI documentation is available at `/docs` while the API is running.

The upload endpoint accepts bounded JSON evidence with `filename`, `category` and `content`. The backend validates the JSON, persists its SHA-256 hash and appends an `evidence.uploaded` event to the workflow audit chain.
