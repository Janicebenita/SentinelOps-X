<p align="center">
  <img src="https://raw.githubusercontent.com/Janicebenita/SentinelOps-X/main/docs/assets/sentinelops-nexus-hero.png" alt="SentinelOps Nexus enterprise operational digital twin" width="100%" />
</p>

<h1 align="center">🛡️ SentinelOps Nexus</h1>

<p align="center"><strong>The Enterprise Operational Digital Twin</strong></p>
<p align="center"><em>Predict tomorrow's operational bottleneck before customers experience it.</em></p>

<p align="center">
  <a href="https://sentinelops-frontend-398391487181.asia-south1.run.app/"><img alt="Google Cloud Run live" src="https://img.shields.io/badge/Google_Cloud_Run-LIVE-4285F4?logo=googlecloud&amp;logoColor=white" /></a>
  <a href="https://github.com/Janicebenita/SentinelOps-X/actions/workflows/validate.yml"><img alt="Validation workflow" src="https://github.com/Janicebenita/SentinelOps-X/actions/workflows/validate.yml/badge.svg?branch=main" /></a>
  <img alt="Human governed" src="https://img.shields.io/badge/Safety-HUMAN_GOVERNED-00A86B" />
  <img alt="Production action not executed" src="https://img.shields.io/badge/Production_Action-NOT_EXECUTED-FF8C00" />
</p>

<p align="center">
  <img alt="React" src="https://img.shields.io/badge/React-Enterprise_UI-149ECA?style=for-the-badge&amp;logo=react&amp;logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Typed_API-009688?style=for-the-badge&amp;logo=fastapi&amp;logoColor=white" />
  <img alt="Google Cloud" src="https://img.shields.io/badge/Google_Cloud-Cloud_Run-4285F4?style=for-the-badge&amp;logo=googlecloud&amp;logoColor=white" />
  <img alt="Gemini" src="https://img.shields.io/badge/Gemini-Evidence_Reasoning-8E75B2?style=for-the-badge&amp;logo=googlegemini&amp;logoColor=white" />
</p>

<p align="center">
  <a href="https://sentinelops-frontend-398391487181.asia-south1.run.app/"><strong>🚀 Open Live Product</strong></a>
  ·
  <a href="https://sentinelops-frontend-398391487181.asia-south1.run.app/command-centre"><strong>🧭 Command Centre</strong></a>
  ·
  <a href="https://sentinelops-frontend-398391487181.asia-south1.run.app/judge-demo"><strong>🎬 Guided Demo</strong></a>
  ·
  <a href="docs/architecture.md"><strong>🏗️ Architecture</strong></a>
</p>

<p align="center">
  <a href="https://sentinelops-frontend-398391487181.asia-south1.run.app/judge-demo">
    <img src="https://raw.githubusercontent.com/Janicebenita/SentinelOps-X/main/docs/assets/sentinelops-nexus-30-second-flow.gif" alt="30-second SentinelOps Nexus flow: forecast, Digital Twin, simulation, Gemini reasoning, Gemma review, human approval, and Evidence ZIP" width="960" />
  </a>
</p>

<p align="center"><strong>Forecast → Digital Twin → Simulation → Gemini Reasoning → Gemma Review → Human Approval → Evidence ZIP</strong></p>
<p align="center"><sub>30-second product flow · click the animation to open the interactive backend-driven demo</sub></p>

> National AI Agent Builder Finale submission for the B2B Services challenge: Late Bottleneck Detection.

> [!IMPORTANT]
> **PRODUCTION ACTION: NOT EXECUTED**
>
> Approval records a governed human decision and enables evidence export.
>
> It does not deploy, scale, roll back, reconfigure, or modify production infrastructure.

## 🌐 Live deployment status

| Environment | Status | Purpose |
|---|---|---|
| Local | `IMPLEMENTED_AND_VERIFIED` | Complete deterministic workflow and reproducible validation |
| Google Cloud Run | `IMPLEMENTED_AND_VERIFIED_LIVE` | Primary live deployment; nine services passed authenticated health and readiness checks |

## 🚀 Live product

- **Primary application:** [Open SentinelOps Nexus on Google Cloud Run](https://sentinelops-frontend-398391487181.asia-south1.run.app/)
- **Command Centre:** [Open the operational workspace](https://sentinelops-frontend-398391487181.asia-south1.run.app/command-centre)
- **Guided product demo:** [Start the deterministic judge workflow](https://sentinelops-frontend-398391487181.asia-south1.run.app/judge-demo)
- Local application: `http://localhost:5173/`
- Local Command Centre: `http://localhost:5173/command-centre`
- Local five-minute evidence workspace: `http://localhost:5173/judge-demo`

Google Cloud Run is the primary live judge-demo environment. The deployed frontend and API passed direct HTTP, runtime-configuration, readiness, and browser CORS checks; all nine Cloud Run service health and readiness endpoints passed the authenticated deployment smoke test.

SentinelOps Nexus is an evidence-driven operational decision-support product. It forecasts emerging Redis saturation, builds a bounded Digital Twin, replays 12 deterministic scenarios, compares FAST, SAFE, and OPTIMAL interventions, applies mandatory safety gates, and stops at an authorized human decision boundary.

| Enterprise signal | Product evidence |
|---|---|
| Operational foresight | Deterministic Redis safe-capacity forecast before the reactive alert |
| Decision confidence | Twelve reproducible scenarios and a transparent intervention tournament |
| AI with bounded authority | Gemini explains; Gemma critiques; deterministic backend gates decide eligibility |
| Human governance | Verified role, mandatory rationale, backend authorization, and no automatic approval |
| Auditability | Evidence references, result hashes, trace context, SHA-256-linked events, and Evidence ZIP |

[Quick Start](#running-locally) | [Architecture](#architecture-summary) | [Guided Demo](#guided-product-demo) | [Safety](#security-and-human-control) | [Evaluation Evidence](#evaluation-evidence)

## 🎯 Project overview

The canonical seeded workflow models a Payment Service whose Redis memory pressure rises before a reactive alert fires. Under the documented deterministic seed, SentinelOps Nexus:

- forecasts the Redis safe-capacity crossing at **+30 minutes**;
- estimates possible customer impact at **+45 minutes**;
- creates a version-locked, content-hashed Digital Twin;
- replays **12 deterministic scenarios**;
- disqualifies FAST when its mandatory failover gate fails;
- recommends the highest-scoring eligible candidate, currently OPTIMAL;
- generates an evidence-grounded executive brief;
- requires a qualified human decision and rationale; and
- exports a verifiable Evidence ZIP with `manifest.sha256`.

The bounded deterministic forecast and mandatory safety gates remain authoritative. Model output cannot approve, change workflow state, override eligibility, or execute a production action.

## 🏗️ Architecture summary

<p align="center">
  <a href="docs/assets/sentinelops-nexus-architecture-readable.png">
    <img src="https://raw.githubusercontent.com/Janicebenita/SentinelOps-X/main/docs/assets/sentinelops-nexus-architecture-readable.png" alt="Readable SentinelOps Nexus safety-first workflow and Google Cloud runtime architecture" width="100%" />
  </a>
</p>

<p align="center"><sub><strong>Complete Google-native enterprise architecture</strong> · click the board for the full-resolution PDF</sub></p>

```mermaid
flowchart LR
    T["Telemetry Ingestion"] --> F["Redis Forecast Service"] --> D["Digital Twin Engine"] --> S["Simulation Engine"] --> O["Optimization Engine"]
    O --> G["Gemini Enterprise Agent Platform<br/>(formerly Vertex AI)"] --> P["Gemma Private Policy Review Engine"]
    P --> M["Mandatory Safety Gates"] --> V["Verification Agent"] --> E["Executive Recommendation Generator"]
    E --> H["AWAITING_HUMAN"] --> A["Human Approval Stage"] --> C["Tamper-Evident SHA-256-Linked Audit Chain"] --> Z["Evidence ZIP Export"]
    classDef deterministic fill:#082f49,stroke:#22d3ee,color:#e0f2fe;
    classDef ai fill:#312e81,stroke:#a78bfa,color:#f5f3ff;
    classDef safety fill:#052e16,stroke:#34d399,color:#dcfce7;
    class T,F,D,S,O deterministic;
    class G,P ai;
    class M,V,E,H,A,C,Z safety;
```

This ordering is a safety invariant. Executive recommendation follows mandatory gates and verification. Human approval follows verification and the explicit `AWAITING_HUMAN` state.

The complete architecture is documented in [docs/architecture.md](docs/architecture.md), presented interactively at `/architecture`, and summarized in the [high-contrast architecture board](docs/assets/sentinelops-nexus-architecture-readable.png).

## 🧠 Google AI lifecycle and authority

SentinelOps Nexus follows the Google-native AI engineering lifecycle in this order:

```mermaid
flowchart LR
    A["Google AI Studio"] --> P["Prompt Management"] --> E["Prompt Evaluation"] --> G["Gemini Runtime"] --> M["Gemma Policy Review"]
    classDef studio fill:#174ea6,stroke:#8ab4f8,color:#fff;
    classDef lifecycle fill:#0f766e,stroke:#5eead4,color:#fff;
    classDef model fill:#4c1d95,stroke:#c4b5fd,color:#fff;
    class A studio;
    class P,E lifecycle;
    class G,M model;
```

### 1. Google AI Studio

Google AI Studio is the prompt-development and evaluation workspace—not the production runtime. It supports iterative design of evidence-grounded tasks before approved prompt assets enter version control. The repository does not claim a verified Studio session without authenticated session evidence.

### 2. Prompt management

Version-controlled assets under `prompts/gemini/`, `prompts/gemma/`, `prompts/schemas/`, and `prompts/evaluations/` define prompt IDs, versions, CRISPE context, evidence inputs, allowed tools, prohibited actions, refusal conditions, strict output schemas, and bounded fallbacks.

### 3. Prompt evaluation

Automated schema and evaluation tests check expected evidence references, structured outputs, safety refusals, deterministic-authority boundaries, and prohibited approval or production behavior before a prompt can support the canonical workflow.

### 4. Gemini Enterprise Agent Platform runtime (formerly Vertex AI)

Gemini Enterprise Agent Platform (formerly Vertex AI) is the primary AI reasoning runtime in the Google-native architecture. When Google credentials are configured, it provides:

- evidence-grounded reasoning;
- contradiction and missing-evidence detection;
- scenario and candidate explanations;
- recommendation synthesis;
- business-impact explanation; and
- executive summaries.

Gemini output is schema-validated, evidence-referenced, hashed, traced, audited, and bounded by deterministic fallback behavior. Gemini never approves, executes production actions, bypasses safety gates, or directly mutates workflow state.

### 5. Gemma Private Policy Review Engine

The Gemma Private Policy Review Engine provides a secondary policy and safety review for:

- recommendation-to-gate consistency;
- evidence completeness;
- policy-violation classification;
- contradiction review; and
- unsafe-recommendation critique.

The Gemma Private Policy Review Engine is advisory. It cannot override Mandatory Safety Gates, approve, change workflow state, or execute production actions.

### Backend authority

The FastAPI backend remains authoritative for:

- deterministic forecasts and scenario calculations;
- intervention eligibility and safety gates;
- workflow-state transitions;
- role verification and approval authorization;
- recording the qualified human decision and rationale;
- the tamper-evident SHA-256-linked audit chain; and
- Evidence ZIP generation.

No model approves a recommendation. Only an authorized human can submit a decision that the backend validates and records.

## 🤝 Agent orchestration

The current AI Workforce uses an ADK-compatible orchestration boundary and agent registry. The official Google ADK runtime has not yet been verified in the authenticated environment, so its current status is `LOCAL_ADAPTER_ONLY`. The boundary coordinates structured agent execution and Agent-to-Agent (A2A) handoffs while the backend retains workflow authority.

The workforce includes:

- Nexus Orchestrator;
- Observer Agent;
- Evidence Agent;
- Process Discovery Agent;
- Prediction Agent;
- Digital Twin Agent;
- Simulation Agent;
- Optimization Agent;
- Verification Agent;
- Business Impact Agent; and
- Executive Agent.

Every visible agent card is clickable and opens a backend-driven workspace. Supported run and rerun actions persist status, duration, retry count, inputs, outputs, evidence references, result hashes, and audit events. Typed A2A messages carry workflow, task, correlation, causation, artifact, evidence, status, and trace metadata without storing hidden chain-of-thought.

The official Google ADK runtime was not available in the validated local environment. Local adapter tests are not presented as official managed-runtime evidence.

## 🧰 Controlled MCP tools

MCP is the authenticated, controlled tool interface used by agents. Implemented read-only and bounded tools cover:

- telemetry and latest-metric retrieval;
- service topology and SLO retrieval;
- incident and evidence retrieval;
- Digital Twin manifest creation;
- scenario execution and result access;
- tournament and gate-result access;
- simulation access;
- business-impact calculation; and
- Evidence ZIP export.

MCP tools use strict schemas, authorization, rate limits, correlation IDs, trace IDs, audit events, safe errors, and idempotency where applicable. No MCP tool can deploy, scale, roll back, reconfigure, execute shell commands, or modify cloud infrastructure.

## 🛰️ Antigravity integration boundary

SentinelOps Nexus includes a typed, read-only Antigravity participant boundary without inventing an unsupported SDK or runtime contract.

| Capability | Current evidence |
|---|---|
| Backend status API | `GET /api/v1/integrations/antigravity/status` |
| Product visibility | Antigravity status is surfaced in the guided evidence workspace |
| Safety | Read-only provider; no workflow mutation, approval, gate override, infrastructure action, or production execution |
| Validation | Provider contract and truthful-status tests run in CI |
| Official runtime | `BLOCKED_BY_PARTICIPANT_ACCESS` because official participant documentation, SDK, endpoint, and credentials are unavailable |

The implemented boundary is `LOCAL_ADAPTER_ONLY`. It returns explicit blocker and fallback metadata and always preserves **PRODUCTION ACTION: NOT EXECUTED**. A local adapter response is never represented as an official Antigravity invocation. See [Antigravity Integration](docs/antigravity-integration.md).

## 🗄️ Data and event architecture

### Transactional workflow state

The backend transactional store is authoritative for workflows, agent executions, verification records, human decisions, and audit-chain state. SQLite provides deterministic local and demonstration persistence. BigQuery is not used as the transactional workflow authority.

### BigQuery analytics

In configured Google Cloud mode, BigQuery is the analytical and historical warehouse for:

- historical telemetry;
- forecast analytics;
- simulation results;
- verification results;
- model-invocation metadata;
- audit exports; and
- evidence metadata.

The repository includes nine partitioned and clustered schemas. Authenticated GitHub OIDC verification has provisioned the dataset, inserted an audit-evidence row, and read it back with a recorded query job ID. BigQuery remains analytical storage; it never becomes authoritative for workflow state.

### Pub/Sub eventing

Pub/Sub is the asynchronous event-backbone target for:

- Telemetry Events;
- Agent Task Events;
- Simulation Events;
- Verification Events;
- Model Invocation Events;
- Evidence Export Events;
- Workflow Status Events; and
- BigQuery Export Events.

Typed event envelopes include idempotency, retry, dead-letter, causation, correlation, and trace metadata. Authenticated GitHub OIDC verification has published, received, and acknowledged a uniquely correlated workflow event. The deterministic local adapter remains available for offline operation.

## ✨ Key features

- Transparent bounded Redis saturation forecast
- Version-locked and content-hashed Digital Twin manifest
- Fixed deterministic seed and 12 reproducible scenarios
- FAST, SAFE, and OPTIMAL intervention tournament
- Mandatory eligibility gates that override score
- Verification Agent with persisted technical and approver checks
- Google AI Studio prompt lifecycle with versioned CRISPE assets and automated evaluations
- Evidence-grounded Gemini reasoning with deterministic fallback
- Gemma Private Policy Review Engine safety-critique boundary
- Clickable, backend-connected AI Workforce
- Typed, persisted, and traced A2A messages
- Authenticated MCP tool gateway
- Role-qualified human decisions with mandatory rationale
- Tamper-evident SHA-256-linked audit chain
- Verifiable Evidence ZIP containing `manifest.sha256`
- Explicit absence of any production execution endpoint

## 🔎 Evaluation evidence

| Key evaluation question | Evidence-backed answer |
|---|---|
| What bottleneck is emerging? | Redis saturation on the Payment Service critical path |
| When is safe capacity crossed? | +30 minutes in the canonical deterministic seed |
| When may customers be affected? | +45 minutes under the displayed assumptions |
| How many scenarios are replayed? | 12 using the same Twin manifest and fixed seed |
| Which false fix is detected? | FAST fails the mandatory failover gate |
| Which strategy is recommended? | The highest-scoring eligible candidate; currently OPTIMAL |
| Is confidence a probability? | No. It is a heuristic evidence score |
| Is revenue exposure guaranteed? | No. It is an operational estimate based on visible inputs |
| Does approval deploy anything? | No. It records a governed human decision and enables evidence export |

## 🎬 Guided product demo

The Judge Demo provides a 20-stage, five-minute interactive workflow with keyboard-accessible stage buttons, direct links, and one persistent, large purpose-first evidence panel. Selecting any stage immediately updates the panel, visible selected state, and `?stage=` URL. Arrow-key navigation, Play, Pause, Previous, Next, Restart, Exit Guided Mode, restrained motion, and explicit fallback or credential states remain available. Every stage first explains its operational purpose, implemented value, and remaining live-operation gap before presenting its backend-supported evidence status. It never submits approval. Its Google Cloud evidence stage explains why each managed integration is retained; missing Cloud Build, Artifact Registry, BigQuery, Pub/Sub, or Trace identifiers are never presented as verified. The command centre also supports manual Explore Mode: operators can change traffic, Redis capacity, application replicas, and dependency latency; load presets; upload operational JSON; replay all 12 backend-calculated scenarios; and inspect the resulting evidence and hashes.

The guided experience never activates approval. The narrated video remains a separate supporting artifact: [demo_storytelling_video.mp4](demo_storytelling_video.mp4).

Frontend routes include:

| Product area | Route |
|---|---|
| Landing page | [Open `/`](https://sentinelops-frontend-398391487181.asia-south1.run.app/) |
| Five-minute Judge Demo | [Open `/judge-demo`](https://sentinelops-frontend-398391487181.asia-south1.run.app/judge-demo) |
| Command Centre | [Open `/command-centre`](https://sentinelops-frontend-398391487181.asia-south1.run.app/command-centre) |
| AI Workforce | [Open `/agents`](https://sentinelops-frontend-398391487181.asia-south1.run.app/agents) |
| Agent Workspace | [Open example `/agents/observer-agent`](https://sentinelops-frontend-398391487181.asia-south1.run.app/agents/observer-agent) — pattern: `/agents/:agentName` |
| Workflow detail | [Open example `/workflows/1`](https://sentinelops-frontend-398391487181.asia-south1.run.app/workflows/1) — pattern: `/workflows/:workflowId` |
| Verification | [Open `/workflows/1/verification`](https://sentinelops-frontend-398391487181.asia-south1.run.app/workflows/1/verification) |
| Human decision | [Open `/workflows/1/approval`](https://sentinelops-frontend-398391487181.asia-south1.run.app/workflows/1/approval) |
| Evidence, audit, and export | [Evidence](https://sentinelops-frontend-398391487181.asia-south1.run.app/workflows/1/evidence) · [Audit](https://sentinelops-frontend-398391487181.asia-south1.run.app/workflows/1/audit) · [Export](https://sentinelops-frontend-398391487181.asia-south1.run.app/workflows/1/export) |
| Architecture, safety, and docs | [Architecture](https://sentinelops-frontend-398391487181.asia-south1.run.app/architecture) · [Safety](https://sentinelops-frontend-398391487181.asia-south1.run.app/safety) · [Docs](https://sentinelops-frontend-398391487181.asia-south1.run.app/docs) |
| Google-stack evidence | [Google stack](https://sentinelops-frontend-398391487181.asia-south1.run.app/google-stack) · [Integrations](https://sentinelops-frontend-398391487181.asia-south1.run.app/integrations) · [Observability](https://sentinelops-frontend-398391487181.asia-south1.run.app/observability) · [Security](https://sentinelops-frontend-398391487181.asia-south1.run.app/security-status) · [Model evaluation](https://sentinelops-frontend-398391487181.asia-south1.run.app/model-evaluation) |

## 📂 Enterprise solution repository

SentinelOps Nexus is organized as a production-style, Google Cloud–native enterprise platform. Each repository module has a clearly defined architectural responsibility across product experience, deterministic intelligence, AI orchestration, cloud delivery, security, observability, and evidence governance.

| Repository module | Enterprise responsibility |
|---|---|
| `frontend/` | React and TypeScript product experience for the Command Centre, Judge Demo, AI Workforce, approval workflow, architecture explorer, and evidence views. |
| `backend/` | FastAPI application implementing governed workflows, deterministic intelligence, Digital Twin logic, safety gates, verification, RBAC, JWT handling, audit-chain logic, evidence generation, provider boundaries, and typed APIs. |
| `services/` | Independently packageable service entry points for orchestration, forecasting, simulation, verification, evidence, Gemma policy review, MCP tooling, and bounded integration adapters. |
| `prompts/` | Version-controlled Gemini and Gemma prompts, CRISPE instructions, output schemas, and evaluation cases supporting the Google AI Studio prompt lifecycle. |
| `deploy/cloud-run/` | Cloud Run service descriptors, frontend routing configuration, and runtime service configuration. |
| `scripts/` | Provisioning, validation, deployment, smoke testing, cloud verification, evidence collection, and operational automation. |
| `sql/` | Partitioned and clustered BigQuery schemas for telemetry, workflows, agent execution, scenarios, verification, model invocations, business impact, audit exports, and forecast evaluation. |
| `docs/` | PRD, architecture, safety, security, deployment, evaluation, observability, runtime-evidence, compliance, and governance documentation. |
| `.github/workflows/` | CI workflows for comprehensive validation and controlled Google Cloud runtime verification. |
| `Dockerfile.*` | Service-specific container definitions for reproducible Cloud Run packaging. |
| `cloudbuild.yaml` | Commit-SHA container build configuration for Cloud Build and Artifact Registry publishing. |

### 🏗️ Repository architecture at a glance

```text
SentinelOps Nexus
│
├── Product experience
│   ├── Command Centre
│   ├── Judge Demo
│   ├── AI Workforce
│   └── Approval and evidence workspaces
│
├── Backend intelligence
│   ├── Workflow engine
│   ├── Redis forecast
│   ├── Digital Twin
│   ├── Simulation and optimization
│   ├── Mandatory Safety Gates
│   └── Verification and audit
│
├── Cloud services
│   ├── API gateway
│   ├── Orchestrator
│   ├── Forecast service
│   ├── Simulation service
│   ├── Verification service
│   ├── Evidence service
│   ├── Gemma service
│   └── MCP server
│
├── Google Cloud delivery
│   ├── Cloud Build
│   ├── Artifact Registry
│   ├── Cloud Run
│   ├── Secret Manager
│   ├── IAM and service accounts
│   ├── BigQuery
│   └── Pub/Sub
│
└── Evidence and governance
    ├── SHA-256 audit chain
    ├── Evidence ZIP
    ├── Prompt library
    ├── Runtime evidence
    └── PRD and architecture documentation
```

## ⚙️ Technology stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, TanStack Query, Recharts |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy |
| Deterministic engine | Python forecasting, Digital Twin, simulation, optimization, safety gates |
| Prompt lifecycle | Google AI Studio workflow, versioned CRISPE prompts, schemas, evaluation cases |
| AI reasoning | Gemini Enterprise Agent Platform (formerly Vertex AI), Gemma Private Policy Review Engine, deterministic fallback |
| Agent protocols | Google ADK boundary, typed A2A, authenticated MCP |
| Transactional persistence | SQLite for the deterministic working build |
| Analytical persistence | BigQuery analytical schemas and credential-gated provision/write/read tooling |
| Async eventing | Pub/Sub provisioning/smoke tooling with local idempotent fallback adapter |
| Observability | OpenTelemetry-compatible trace metadata, Cloud Logging, Cloud Monitoring, Cloud Trace targets |
| Cloud delivery | GitHub Actions, Cloud Build, Artifact Registry, Cloud Run, Secret Manager, IAM, ADC |
| Quality | Pytest, Vitest, Ruff, MyPy, Bandit, dependency and secret scanning |

## 🔐 Security and human control

Security controls include:

- OAuth2/OIDC-ready configuration;
- signed, short-lived JWT role tokens;
- backend-authoritative RBAC;
- backend authorization for every human decision;
- least-privilege Cloud Run IAM design;
- Secret Manager references for deployed secrets;
- rate limiting and request-size limits;
- replay protection and idempotency controls;
- strict Pydantic validation, CORS, and security headers;
- mandatory rationale for Senior Developer approval; and
- explicit model and tool non-authority.

Trial credentials are for demonstration only:

| Role | Trial code | Approval behavior |
|---|---:|---|
| Intern | `0000` | May inspect and simulate; cannot approve |
| Senior Developer | `1111` | May approve only after role verification and with mandatory rationale |

Production deployments must replace trial credentials with enterprise identity, SSO, and managed RBAC. Codes remain server-side and must never be bundled into frontend assets, persisted in plaintext, logged, returned, or exported.

## 📡 Observability

The architecture propagates request IDs, correlation IDs, trace IDs, and AI invocation IDs through HTTP, agent, A2A, MCP, model, simulation, verification, authorization, decision, and evidence flows. Services emit structured logs with those identifiers where configured.

OpenTelemetry is the instrumentation boundary. Where Google Cloud credentials and exporters are configured, telemetry targets Cloud Logging, Cloud Monitoring, and Cloud Trace. The local build verifies trace propagation and invocation metadata; it does not claim exported Google Cloud traces without a live trace ID.

Secrets, trial codes, API keys, hidden chain-of-thought, unredacted prompts, and sensitive evidence payloads must not be logged.

## ☁️ Deployment

Google Cloud Run is the primary deployment target. The release pipeline and connected runtime services are:

```text
GitHub
  ↓
GitHub Actions
  ↓
Cloud Build
  ↓
Artifact Registry
  ↓
Cloud Run
  ├── Secret Manager
  ├── BigQuery
  ├── Pub/Sub
  ├── Cloud Logging
  ├── Cloud Monitoring
  ├── Cloud Trace
  ├── IAM / Service Accounts
  └── Application Default Credentials
```

Cloud Build builds commit-SHA-tagged service images. Artifact Registry stores those images. Cloud Run deploys revisions from those stored images. The existence of `cloudbuild.yaml`, Dockerfiles, or deployment manifests is configuration evidence—not proof that an image was pushed or a Cloud Run revision was deployed.

The runtime architecture uses Application Default Credentials (ADC), Cloud Run service accounts, least-privilege IAM, Secret Manager references, and GitHub OIDC with Workload Identity Federation. No service-account JSON key or frontend API key is required.

Nine independently packaged Cloud Run services are defined and deployed:

- `sentinelops-frontend`
- `sentinelops-api-gateway`
- `sentinelops-orchestrator`
- `sentinelops-forecast-service`
- `sentinelops-simulation-service`
- `sentinelops-verification-service`
- `sentinelops-evidence-service`
- `sentinelops-gemma-service`
- `sentinelops-mcp-server`

Cloud Run deployment is `IMPLEMENTED_AND_VERIFIED`: live service URLs and revisions exist, deployment IAM updates completed, every service passed health and readiness smoke checks, and the public frontend-to-API runtime configuration and CORS path were verified.

## 🐳 Container and delivery validation

The production packaging was revalidated locally without changing or redeploying Google Cloud resources:

- Nine production container images build successfully.
- Frontend `/` and `/command-centre` return HTTP 200 in container validation.
- All eight backend services pass both `/health` and `/readiness`.
- `.dockerignore` reduces build context from approximately 448 MB to approximately 290 KB.
- pnpm Docker build compatibility is validated across the project's supported pnpm workflow.
- No production-execution route exists.
- No source or frontend-bundle secret findings were detected in the final safety scan.

Validated images:

- `sentinelops-frontend`
- `sentinelops-api-gateway`
- `sentinelops-orchestrator`
- `sentinelops-forecast`
- `sentinelops-simulation`
- `sentinelops-verification`
- `sentinelops-evidence`
- `sentinelops-gemma`
- `sentinelops-mcp`

Container build context was reduced from approximately 448 MB to approximately 290 KB using `.dockerignore`, improving build throughput and reducing unnecessary source transfer. This is build-pipeline evidence, not an application runtime-performance claim.

The container validation requires no service-account JSON key. Deployed secrets remain external to images and frontend assets and are supplied through Secret Manager and service identity where applicable. The permanent safety invariant remains **PRODUCTION ACTION: NOT EXECUTED**.

## 💻 Running locally

### Prerequisites

- Python 3.11+
- Node.js 20+
- pnpm

### Backend

```powershell
python -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"
& ".\.venv\Scripts\python.exe" -m uvicorn backend.app.main:app --reload --port 8000
```

### Frontend

```powershell
Set-Location frontend
pnpm install
pnpm dev
```

Open:

- Landing page: `http://localhost:5173/`
- Command Centre: `http://localhost:5173/command-centre`
- API documentation: `http://localhost:8000/docs`

The complete deterministic local workflow runs without paid AI credentials. Missing managed providers activate visible, bounded fallback behavior rather than fabricated cloud success.

## ☁️ Running on Google Cloud

Prerequisites are an authenticated Google Cloud CLI, billing access to `sentinelops-nexus-finale`, and the approved `asia-south1` region.

```bash
export PROJECT_ID=sentinelops-nexus-finale
export REGION=asia-south1

bash scripts/provision_google_cloud.sh
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_REGION=asia-south1,COMMIT_SHA=$(git rev-parse HEAD) .
REVISION=$(git rev-parse HEAD) bash scripts/deploy_cloud_run.sh

python scripts/smoke_cloud_run.py
python scripts/smoke_bigquery.py
python scripts/smoke_pubsub.py
bash scripts/verify_google_cloud.sh
```

Provisioning creates secret containers but never creates or prints secret values. Add approved Secret Manager versions before deployment. Do not claim deployment success unless all authenticated smoke checks pass and their non-secret evidence IDs are recorded.

## 🧪 Testing

### Backend, security, and end-to-end

```powershell
& ".\.venv\Scripts\python.exe" -m pytest backend\tests demo_app\tests -q
& ".\.venv\Scripts\python.exe" -m ruff check backend demo_app scripts
& ".\.venv\Scripts\python.exe" -m mypy backend demo_app scripts
& ".\.venv\Scripts\python.exe" -m bandit -q -lll -r backend demo_app scripts
& ".\.venv\Scripts\python.exe" scripts\nexus_e2e.py
```

Coverage evidence is diagnostic rather than a vanity threshold:

```powershell
& ".\.venv\Scripts\python.exe" -m pytest backend\tests demo_app\tests --cov=backend --cov=demo_app --cov-report=term-missing --cov-report=xml
```

### Frontend

```bash
cd frontend
pnpm test
pnpm run coverage
pnpm run build
```

Tests cover deterministic forecasts, scenarios, mandatory gates, agent execution, A2A and MCP contracts, Gemini Enterprise Agent Platform (formerly Vertex AI) and Gemma Private Policy Review Engine authority boundaries, JWT issuer/audience and replay rejection, role verification, Intern rejection, Senior rationale requirements, audit-chain validation, Evidence ZIP verification, interactive frontend routes, and absence of production or infrastructure-mutation endpoints.

## 🔄 CI/CD

`.github/workflows/validate.yml` separates Python quality, frontend quality, security, protocol/AI, nine container builds, and end-to-end validation into independently diagnosable jobs. It publishes non-secret coverage, security, and E2E summaries while proving that compiled frontend assets contain no server-side credential names and that no production-execution route exists.

`.github/workflows/google-cloud-runtime.yml` is a protected `workflow_dispatch` workflow using GitHub OIDC and Workload Identity Federation. Paid or state-changing cloud checks are not run automatically on every pull request. Authenticated runs collect non-secret Cloud Run, BigQuery, Pub/Sub, Cloud Logging, observability-API, and inventory evidence as short-retention artifacts.

## ✅ Implementation and verification

| Readiness area | Product outcome |
|---|---|
| Operational intelligence | ✅ Deterministic forecast, Digital Twin, 12-scenario replay, tournament, safety gates, and verification pass reproducibly. |
| Human control | ✅ Intern approval is blocked; a verified Senior Developer and mandatory rationale are required; no production action is executed. |
| Live Google Cloud platform | ✅ Nine Cloud Run services, Cloud Build images, Artifact Registry, IAM, Secret Manager, BigQuery write/read, and Pub/Sub publish/receive/acknowledge are live-verified. |
| AI assurance | 🛡️ Gemini and Gemma remain explanation and policy-review boundaries; deterministic policy and backend authorization stay authoritative even when managed-model evidence is unavailable. |

<details>
<summary><strong>View the detailed evidence-backed component matrix</strong></summary>

> **Evidence rule:** Status labels reflect only capabilities verified at the stated boundary; configuration or source code alone is not treated as managed-runtime proof.

| Component | Current status | Evidence boundary |
|---|---|---|
| Deterministic operational intelligence | `IMPLEMENTED_AND_VERIFIED` | Forecast, Digital Twin, 12 scenarios, intervention tournament, and mandatory gates pass reproducible end-to-end tests. |
| Governed human decision and evidence | `IMPLEMENTED_AND_VERIFIED` | Intern blocking, Senior rationale, backend authorization, audit-chain verification, and Evidence ZIP validation pass. |
| Production container packaging and service health | `IMPLEMENTED_AND_VERIFIED` | All nine production images built successfully; frontend key routes returned HTTP 200; all eight backend services passed `/health` and `/readiness`; final secret and forbidden-route scans passed. |
| Judge Demo | `IMPLEMENTED_AND_VERIFIED_LIVE` | The deployed 20-stage experience uses semantic stage controls, URL-addressable state, a dynamic explanation panel, guided playback, and automated interaction tests. |
| Interactive architecture explorer | `IMPLEMENTED_AND_VERIFIED_LIVE` | The deployed route provides clickable domains, URL state, authority boundaries, BigQuery/Pub/Sub flows, Cloud Run services, and automated interaction tests. |
| Google AI Studio prompt lifecycle | `IMPLEMENTED_REQUIRES_RUNTIME_EVIDENCE` | Thirteen CRISPE prompt assets, schemas, and evaluations are version controlled; an authenticated AI Studio session artifact is not claimed. |
| Gemini Enterprise Agent Platform (formerly Vertex AI) | `IMPLEMENTED_REQUIRES_RUNTIME_EVIDENCE` | Evidence-grounded reasoning, schema validation, metadata capture, and bounded fallback are implemented; a managed invocation ID is still required for live model verification. |
| Gemma Private Policy Review Engine | `RUNTIME_EVIDENCE_REQUIRED` | The policy service is deployed and healthy on Cloud Run with a safe advisory fallback; managed Gemma model-invocation evidence is not yet claimed. |
| Google ADK boundary | `LOCAL_ADAPTER_ONLY` | The tested agent registry and orchestration contract preserve backend authority; the official ADK runtime has not been independently evidenced. |
| A2A handoffs | `IMPLEMENTED_AND_VERIFIED` | Typed messages are persisted, correlated, traced, retried, and covered by protocol tests. |
| MCP controlled tools | `IMPLEMENTED_AND_VERIFIED_LIVE` | The authenticated 13-tool gateway is deployed and healthy; schemas, authorization, audit, rate limits, and no-infrastructure-mutation behavior are tested. |
| Managed supplemental forecasting | `LOCAL_FALLBACK_AVAILABLE` | The supplemental provider boundary is available while the deterministic bounded forecast remains authoritative. |
| BigQuery infrastructure | `IMPLEMENTED_AND_VERIFIED_LIVE` | Dataset and nine physical analytical tables were provisioned in `sentinelops-nexus-finale`. |
| BigQuery write/read path | `IMPLEMENTED_AND_VERIFIED_LIVE` | [Authenticated workflow #14](https://github.com/Janicebenita/SentinelOps-X/actions/runs/31140376799) inserted evidence row `smoke-c5c11478-5b8d-43c2-bee5-e3223e000bac` and read it with query job `sentinelops_smoke_85ef5547783b49249e05043d42800030`. |
| Pub/Sub event path | `IMPLEMENTED_AND_VERIFIED_LIVE` | The same authenticated run published, received, and acknowledged message `20178966799882394` on `sentinelops-workflow-events`. |
| Cloud Run | `IMPLEMENTED_AND_VERIFIED_LIVE` | Nine services expose live revisions and passed authenticated health and readiness checks in workflow #14. |
| Artifact Registry and Cloud Build | `IMPLEMENTED_AND_VERIFIED_LIVE` | Commit-SHA container images were built, published, and used by the deployed Cloud Run revisions. |
| Secret Manager | `IMPLEMENTED_AND_VERIFIED_LIVE` | Enabled secret versions are consumed through Cloud Run secret references; secrets are not embedded in images or frontend assets. |
| IAM and service accounts | `IMPLEMENTED_AND_VERIFIED_LIVE` | Dedicated service identities, least-privilege bindings, and GitHub Workload Identity Federation are active. |
| OpenTelemetry instrumentation | `IMPLEMENTED_AND_VERIFIED_LOCAL` | Request, correlation, trace, and AI invocation metadata propagation is covered by local tests. |
| Cloud Logging | `IMPLEMENTED_AND_VERIFIED_LIVE` | Structured Cloud Run application and revision logs have been retrieved during live deployment validation. |
| Cloud Monitoring | `IMPLEMENTED_REQUIRES_RUNTIME_EVIDENCE` | Monitoring integration is configured; a captured live metric or dashboard artifact remains required. |
| Cloud Trace | `IMPLEMENTED_REQUIRES_RUNTIME_EVIDENCE` | Trace propagation is implemented; an exported Google Cloud trace ID remains required. |
| OAuth2/OIDC boundary | `LOCAL_ADAPTER_ONLY` | OIDC-ready configuration exists; enterprise identity-provider sign-in is not presented as active. |
| JWT and backend RBAC | `IMPLEMENTED_AND_VERIFIED` | Short-lived token validation, Intern rejection, Senior authorization, and mandatory rationale are tested. |
| Antigravity boundary | `LOCAL_ADAPTER_ONLY` | A tested read-only contract exists; runtime condition remains `BLOCKED_BY_PARTICIPANT_ACCESS` until an official participant API, SDK, or credential is supplied. |

</details>

## 📚 Documentation links

| Document | Purpose |
|---|---|
| [Product Requirements Document](docs/PRD.md) | Product scope, requirements, acceptance criteria, and limitations |
| [Architecture](docs/architecture.md) | Components, service boundaries, authority, and data flow |
| [Runtime Evidence Index](docs/runtime-evidence-index.md) | Local, CI, cloud, and credential evidence boundaries |
| [Judge Compliance Matrix](docs/judge-compliance-matrix.md) | Requirement-to-source/test/evidence traceability |
| [AI Workforce](docs/agent-workforce.md) | Agent responsibilities and workspace behavior |
| [Verification Agent](docs/verification-agent.md) | Technical and approver qualification checks |
| [Approval and RBAC](docs/approval-and-rbac.md) | Trial roles, signed tokens, and decision policy |
| [MCP Runtime](docs/mcp-runtime.md) | Controlled tool contracts and safety restrictions |
| [Google AI Studio Workflow](docs/google-ai-studio-workflow.md) | CRISPE prompt lifecycle and evidence boundary |
| [Antigravity Integration](docs/antigravity-integration.md) | Mandatory participant boundary and exact access blocker |
| [BigQuery Schema](docs/bigquery-schema.md) | Physical analytical DDL and authenticated smoke procedure |
| [Pub/Sub Eventing](docs/pubsub-eventing.md) | Topics, delivery controls, and smoke procedure |
| [A2A Runtime](docs/a2a-runtime.md) | Typed communication, persistence, and trace propagation |
| [Cloud Run Deployment](docs/cloud-run-deployment.md) | Google Cloud deployment and rollback guidance |
| [Security Architecture](docs/security-architecture.md) | Authentication, authorization, secrets, and threat controls |
| [Configuration](docs/configuration.md) | Typed environment variables, classifications, sources, and fail-closed behavior |
| [Testing Strategy](docs/testing.md) | Business, API, security, provider, frontend, and cloud-contract test layers |
| [CI/CD Controls](docs/ci-cd.md) | Validation jobs, protected runtime verification, artifacts, and rollback |
| [Observability](docs/observability.md) | Trace, logging, monitoring, and redaction boundaries |
| [Evaluation Q&A](docs/technical-qa.md) | Internal evaluation preparation |
| [Making SentinelOps Nexus](docs/making-of-sentinelops-nexus.md) | Human-led creation story, encountered bugs, and rectifications |

## ⚠️ Known limitations

- Managed Gemini Enterprise Agent Platform (formerly Vertex AI), managed Gemma inference, Cloud Monitoring, and exported Cloud Trace evidence still require their individual authenticated runtime proof. BigQuery write/read, Pub/Sub publish/receive/acknowledge, and Cloud Run health/readiness are verified live by authenticated workflow #14.
- The official Google ADK runtime was unavailable in the validated environment, so the working orchestration boundary remains a local adapter.
- Included telemetry is deterministic seeded demonstration data, not a live enterprise feed.
- The bounded linear forecast is transparent and reproducible, not a calibrated probability.
- The Digital Twin is a bounded operational model under documented assumptions, not a complete production replica.
- Business-impact results are operational estimates, not guaranteed savings or accounting results.
- SQLite is appropriate for deterministic local operation but is not a durable distributed production store.
- The tamper-evident SHA-256-linked audit chain detects changes; it is not certified immutable storage.
- Trial access codes are demonstration credentials and must be replaced by enterprise SSO and RBAC.
- No production execution endpoint exists.

## 👤 Author

Built by **[Janice Benita F](https://github.com/Janicebenita)** for the **National AI Agent Builder Finale**.

**Predict early. Simulate safely. Decide with evidence.**
