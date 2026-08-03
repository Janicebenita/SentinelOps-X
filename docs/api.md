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

Invalid state transitions return HTTP `409` with the expected state. Model/provider outputs never directly change workflow state.

## Human decision

- `POST /api/v1/workflows/{id}/approve`
- `POST /api/v1/workflows/{id}/reject`
- `POST /api/v1/workflows/{id}/request-evidence`

Each endpoint requires a matching typed decision, named actor and rationale. Approval records a decision and enables evidence export only.

## Evidence and audit

- `GET /api/v1/workflows/{id}/evidence`
- `GET /api/v1/workflows/{id}/agents`
- `GET /api/v1/workflows/{id}/timeline`
- `GET /api/v1/workflows/{id}/events` (SSE snapshot)
- `GET /api/v1/workflows/{id}/export`
- `GET /api/v1/audit/verify?run_id={id}`

Interactive OpenAPI documentation is available at `/docs` while the API is running.
