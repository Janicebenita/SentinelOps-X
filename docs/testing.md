# Testing strategy

SentinelOps Nexus uses deterministic fixtures and boundary-focused tests. Coverage is reported as diagnostic evidence; there is no arbitrary percentage gate.

## Layers

- **Business logic:** seeded telemetry, +30-minute capacity crossing, +45-minute impact estimate, Digital Twin/hash stability, 12 scenarios, tournament scoring, and eligibility-over-score policy.
- **API and authorization:** workflow transitions, malformed/expired JWTs, issuer/audience validation, Intern HTTP 403, Senior rationale, decision replay rejection, request limits, and safe errors.
- **Safety and providers:** Gemini/Gemma advisory boundaries, deterministic fallback, schema/time-out failures, ADK/A2A/MCP contracts, and absence of production/infrastructure mutation routes.
- **Evidence:** audit hash linkage, tamper detection, workflow/evidence correlation, Evidence ZIP contents, and `manifest.sha256` verification.
- **Frontend components:** network-boundary fixtures verify Judge Demo interaction, Architecture selection, approval errors, and evidence locking without testing private component state.
- **Cloud contracts:** BigQuery DDL, Pub/Sub envelopes, Cloud Run environment/PORT/health/readiness, IAM, Secret Manager references, and OIDC workflow configuration.

## Commands

```bash
python -m pytest backend/tests demo_app/tests -q
python -m pytest backend/tests demo_app/tests --cov=backend --cov=demo_app --cov-report=term-missing --cov-report=xml
python -m ruff check backend demo_app scripts
python -m mypy backend demo_app scripts
python -m bandit -q -lll -r backend demo_app scripts

cd frontend
pnpm exec tsc --noEmit
pnpm test
pnpm run coverage
pnpm run build
```

Managed-runtime smoke tests are separate because configuration and local mocks are not proof of a live cloud invocation.
