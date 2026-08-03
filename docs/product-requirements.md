# SentinelOps Nexus Product Requirements Document

## Document control

| Field | Value |
|---|---|
| Product | SentinelOps Nexus |
| Category | Enterprise operational decision-support software |
| Version | 2.0 |
| Status | Implemented demonstration baseline |
| Owner | Janice Benita F |
| Challenge | B2B Services — Late Bottleneck Detection |

## Product vision

SentinelOps Nexus helps operations teams identify an emerging service constraint before it becomes a customer-facing incident. It converts telemetry, topology, capacity, configuration, service-level objectives and business assumptions into a bounded Operational Digital Twin. The product forecasts threshold crossings, replays deterministic future and failure scenarios, compares interventions under identical conditions and stops at a human decision boundary.

## Problem statement

Traditional operational tooling is primarily reactive: it alerts after latency or error thresholds have already been crossed. Operators must then correlate fragmented evidence, estimate impact and compare mitigations while the incident is developing. This creates delayed detection, unsafe first fixes and decisions that are difficult to reproduce or audit.

The product must answer five questions with linked evidence:

1. Which operational bottleneck is emerging?
2. When will safe capacity be crossed?
3. When may customers be affected?
4. Which intervention remains safe under nearby failure conditions?
5. What technical and commercial exposure follows from the documented assumptions?

## Target users

- Site reliability engineers and platform engineers investigating capacity risk.
- Incident commanders comparing mitigations before customer impact.
- Service owners responsible for SLOs, dependencies and operational readiness.
- Engineering and operations leaders reviewing technical and business exposure.
- Auditors or evaluators verifying evidence, reproducibility and human control.

## Primary user journey

1. The operator opens the command centre or Guided Product Demo.
2. Nexus loads a persisted workflow and its evidence-linked forecast.
3. The operator reviews Yesterday, Now, +15, +30 and +45-minute telemetry.
4. The operator selects a preset, adjusts bounded controls or uploads operational JSON.
5. The backend creates an immutable Twin manifest and calculates 12 scenarios.
6. The operator inspects scenario inputs, status, latency, error rate, recovery estimate and deterministic hash.
7. Nexus applies mandatory gates before ranking FAST, SAFE and OPTIMAL interventions.
8. The operator reviews the recommendation, uncertainty and estimated business exposure.
9. A named human approves, rejects or requests more evidence.
10. Approval records the decision and enables evidence export; it never performs a production action.

## Functional requirements

### FR-1 — Evidence ingestion

- Accept deterministic seeded telemetry for the canonical demonstration.
- Accept bounded operational JSON up to 256 KB through the Explore Mode file chooser.
- Validate imported control values before simulation.
- Persist uploaded evidence with its source, category, timestamp and SHA-256 content hash.
- Append upload activity to the tamper-evident audit chain.

### FR-2 — Forecasting

- Calculate Redis saturation from traffic, capacity, replica and dependency-latency controls.
- Display the forecasting method, equation, safe threshold, residual MAE, error bound and assumptions.
- Report threshold crossing and customer-impact times separately.
- Label confidence as a heuristic evidence score, not a probability.

### FR-3 — Operational Digital Twin

- Produce a versioned, immutable manifest containing configuration, topology, telemetry, seed, resource limits and network policy.
- Hash the manifest and expose the hash in the UI and evidence package.
- Keep the model bounded by documented assumptions and resource limits.

### FR-4 — Scenario laboratory

- Calculate 12 deterministic scenarios from the submitted controls.
- Include growth, cache failure, dependency latency, failover, stress, capacity, rollback, rate limiting, cache-policy and configuration-drift conditions.
- Return inputs, status, p95 latency, error rate, recovery estimate, evidence references and deterministic result hash for every scenario.
- Produce identical hashes for identical manifests, controls and seeds.

### FR-5 — Intervention tournament

- Compare FAST, SAFE and OPTIMAL interventions against the same Twin.
- Apply mandatory eligibility gates before score-based ranking.
- Prevent an ineligible candidate from being recommended regardless of score.
- Display cost, risk, recovery time, reversibility, gates, score and verdict.

### FR-6 — Business impact

- Estimate customers, orders and revenue exposure using visible inputs and equations.
- Clearly label results as operational estimates rather than guaranteed loss or savings.

### FR-7 — Human decision and export

- Require a named actor, decision and rationale.
- Support approve, reject and request-more-evidence outcomes.
- Preserve `PRODUCTION ACTION: NOT EXECUTED` throughout the workflow.
- Permit evidence ZIP export only after the recorded decision state allows it.
- Include manifest hashes and an auditable event chain in the export.

### FR-8 — Product modes

- Provide an auto-playing Guided Product Demo that can be paused, navigated or exited.
- Ensure Guided Product Demo never activates approval.
- Provide Explore Mode with presets, sliders, upload, rerun and scenario selection.
- Keep the narrated video separate from the working application and linked only as supporting material.

## Non-functional requirements

- **Reproducibility:** identical inputs and seeds produce identical Twin and scenario hashes.
- **Safety:** no endpoint or UI action executes a production deployment or infrastructure change.
- **Auditability:** material transitions and manual evidence uploads are persisted in a chained SHA-256 timeline.
- **Accessibility:** interactive controls have accessible names, keyboard focus indicators and reduced-motion support.
- **Responsiveness:** the command centre supports desktop and narrow-screen layouts.
- **Portability:** local, Docker Compose and Render Blueprint execution paths are supported.
- **Security:** inputs are typed and bounded; network access inside the Twin is disabled; static security checks run in CI.
- **Availability:** public health and readiness endpoints expose service state independently of the frontend.

## Data and API requirements

- FastAPI exposes the versioned workflow under `/api/v1`.
- SQLAlchemy persists runs, evidence and audit events; SQLite is used by the demonstration baseline.
- The frontend obtains all material workflow results from the API rather than embedding calculated outcomes.
- Invalid state transitions return a conflict response and cannot bypass policy order.
- The public API contract is documented in [`api.md`](api.md) and interactive OpenAPI documentation.

## Acceptance criteria

The release is acceptable when:

- A fresh workflow reaches `RECOMMENDED` after the backend calculates 12 scenarios.
- Changing bounded controls changes forecast or scenario results and deterministic hashes.
- Operational JSON upload is validated, hashed, persisted and visible in the audit timeline.
- FAST fails its mandatory failover gate and cannot be selected solely because of score.
- A human decision never changes `production_action_executed` to true.
- The evidence ZIP validates every included artifact against `manifest.sha256`.
- Backend tests, frontend tests, type checking, lint, security scanning, production build and E2E validation pass in CI.
- The deployed frontend, API and simulator health endpoints respond successfully.

## Success measures

- Time from workflow creation to evidence-backed recommendation.
- Percentage of material claims linked to persisted evidence.
- Scenario reproducibility rate across identical runs.
- False-fix detection count and unsafe-action rate.
- Mandatory approval bypass count, expected to remain zero.
- Production actions executed by Nexus, required to remain zero in this release.

## Current scope and limitations

- The public dataset is deterministic seeded demonstration telemetry, not a live enterprise feed.
- The forecast is a transparent bounded model, not a calibrated probability model.
- Business impact is an estimate under displayed assumptions.
- SQLite storage on Render free services is ephemeral.
- Enterprise observability, Google ADK, A2A, MCP, Vertex AI and production infrastructure connectors remain future integrations unless separately configured and demonstrated.

## Deployment and operations

- Live software: [SentinelOps Nexus](https://janicebenita-sentinelops-nexus.onrender.com)
- Versioned API: [API health](https://janicebenita-sentinelops-nexus-api.onrender.com/api/v1/health)
- Simulator: [Simulator health](https://janicebenita-sentinelops-nexus-simulator.onrender.com/health)
- Source repository: [GitHub](https://github.com/Janicebenita/SentinelOps-X)
- Local Windows launcher: `start-sentinelops.cmd`

## Future evolution

1. Replace ephemeral SQLite with managed PostgreSQL.
2. Add authenticated tenant and role boundaries.
3. Connect production telemetry and topology providers behind explicit adapters.
4. Calibrate forecasting models against historical incidents.
5. Add controlled notification and ticketing integrations without weakening the human approval boundary.
6. Add deployment-provider integrations only as separately permissioned, policy-gated workflows.
