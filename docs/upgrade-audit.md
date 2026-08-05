# SentinelOps Nexus Upgrade Audit

Date: 5 August 2026

## Existing product

The repository is an operational React 18, TanStack Query, FastAPI, SQLAlchemy and SQLite product. The Nexus workflow already observes evidence, forecasts Redis saturation, builds a bounded Digital Twin, calculates 12 deterministic scenarios, ranks FAST/SAFE/OPTIMAL interventions, verifies mandatory gates, estimates business impact, creates an executive brief, records a human decision, maintains a chained SHA-256 audit log and produces a one-time evidence ZIP. `PRODUCTION ACTION: NOT EXECUTED` is persisted and displayed.

## Workforce inventory

The command-centre rail currently derives cards from audit-event envelopes. It contains Nexus Orchestrator, Observer, Prediction, Digital Twin, Simulation, Optimisation, Verification, Business Impact, Executive and Human Approval Gateway entries. Evidence and Process Discovery are implicit in Observer/topology processing, not first-class cards. Cards are plain navigation anchors, not Agent Workspaces. There are no per-agent run/rerun APIs, persisted execution durations, retry counts or structured error records.

Existing real actions are workflow creation, observation, prediction, twin creation, simulation, tournament, verification, impact calculation, recommendation, decision, evidence upload/export and audit verification. Missing actions are workforce catalogue/detail/status, individual agent execution/rerun, agent event retrieval, first-class Evidence and Process Discovery agents, and persisted agent execution metadata.

## Approval and authorization

The current frontend submits a fixed `finale-judge` actor and rationale. The backend validates workflow state but has no authenticated role, signed token or approver qualification. Any caller reaching the endpoint can approve. Access codes are not implemented. Decisions live in `NexusRun.human_decision_json`; there are no RoleVerification, HumanDecision or VerificationRecord tables. This is the principal authorization weakness.

## Audit and evidence

`NexusAuditEvent` chains canonical event bodies with SHA-256 previous/current hashes. Evidence export is one-time, marks the decision as consumed and appends `evidence.exported`. Existing behavior is sound and must be extended without storing access codes or enabling production execution.

## Frontend routes and performance

There is one `App.tsx`, no router and no route code splitting. The initial production bundle is 610,943 bytes JavaScript and 21,144 bytes CSS before transport compression. Initial command-centre rendering requests bootstrap followed by telemetry, evidence, timeline and agents: five critical requests. Recharts and the entire command centre are in the first bundle. Evidence, audit and agent details are fetched before they are needed. Agent cards are not interactive workspaces.

## Backend startup and API performance

Importing `backend.app.main` synchronously creates all tables and seeds the legacy demo. Local measured import/startup baseline: 6,082.84 ms. `/health` performs a database query, outbound simulator health request, sandbox discovery and provider construction; measured local latency: 1,506.39 ms. Nexus bootstrap itself measured 25.17 ms warm with a 19,181-byte response. Cold Render instances can add 50 seconds or more, as Render reports for the free plan. The external dependency check makes health unsuitable for orchestration.

## Dependencies and deployment

Recharts is the largest non-framework frontend dependency and is loaded eagerly. Lucide imports are tree-shakeable. Backend dependencies are moderate; `uvicorn[standard]` and development tools are installed on the Render API because the build uses `.[dev]`. Render uses ephemeral SQLite in `/tmp`; data is not durable. SPA rewrite already exists. Static assets lack explicit immutable cache headers. CI runs tests, lint, typecheck, Bandit, frontend build and E2E, but lacks explicit authorization, compiled-code credential, secret and dependency checks.

## Documentation mismatches

README describes the product well but does not document landing/command-centre routes, Agent Workspaces, role verification, trial roles, token expiry or the new workforce APIs. Existing validation documentation predates this upgrade. The narrated video remains separate and must not replace the software.

## Upgrade constraints

- Preserve deterministic calculation and existing API compatibility where practical.
- Treat legacy `RECOMMENDED` runs as awaiting human review.
- Never expose chain-of-thought; show structured evidence, assumptions, decisions and outputs.
- Never persist, log, return or bundle plaintext access codes.
- Keep backend authorization authoritative.
- Keep production execution disabled and provide no production execution endpoint.

