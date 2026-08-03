# SentinelOps Nexus implementation plan

## Baseline audit

The inherited repository starts successfully and its existing checks pass: 36 backend/demo tests, two frontend tests, Ruff, MyPy, Bandit, and the Vite production build. It also retains valuable SentinelOps safety primitives: an allowlisted sandbox, provider adapters with deterministic fallback, a transition validator, evidence records, human approval, and chained package hashes.

The current Nexus path is not yet the required product. It is a single non-versioned, non-persisted calculated endpoint consumed by one large React component. Agent outputs are untyped dictionaries; there is no Nexus workflow state, live persisted event stream, approval action, Nexus evidence package, or P0 E2E. The timeline has seven points rather than the required Yesterday/Now/+15/+30/+45 contract. Only four chaos scenarios exist. The inherited primary API, scripts, demo video generator, and several documents still describe TN checkout repair. Docker Compose also uses inconsistent frontend environment naming. The README contains encoding defects and does not document the complete requested surface.

## Implementation sequence

1. Add Pydantic v2 contracts for telemetry, evidence, forecasts, topology, manifests, scenarios, strategies, gates, impact, decisions, and agent envelopes.
2. Add JSON-backed SQLAlchemy persistence for Nexus runs, evidence, and chained audit events while preserving existing tables for the secondary reactive workflow.
3. Implement a deterministic Nexus orchestrator with a validated state machine and twelve bounded agent stages.
4. Implement the required five-point telemetry timeline, transparent forecast, ten scenarios, three differentiated interventions, ten mandatory gates, deterministic eligibility and scoring, impact equations, approval boundary, audit verification, and ZIP export.
5. Expose the workflow through `/api/v1`, including health/readiness, reset/seed, step endpoints, run-all, SSE events, export, and chain verification.
6. Replace the frontend's single calculation call with the persisted workflow contract, interactive time travel and twin controls, gate matrix, audit timeline, approval, and export.
7. Replace inherited primary-path scripts and documentation with Nexus commands while keeping reactive components explicitly secondary.
8. Validate clean reset-to-export E2E, all tests, lint, typing, Bandit, frontend tests/build, backend startup, and audit tamper detection.

## Safety decisions

- Approval only records a human decision and enables evidence export.
- There is no production execution or deployment route.
- Failed mandatory gates always make a strategy ineligible before scoring.
- Forecast and commercial values expose equations and assumptions.
- Confidence remains a heuristic evidence score.
- The Twin is described as a bounded operational model, never a perfect replica.
- External provider and ADK/A2A compatibility remain optional adapters; local deterministic mode is authoritative for the demo.
