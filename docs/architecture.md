# SentinelOps Nexus Architecture

## Google-native target boundary

```mermaid
flowchart LR
  UI["React frontend / Cloud Run"] --> GW["FastAPI API gateway / OAuth2-JWT ready"]
  GW --> ADK["ADK orchestrator adapter"]
  ADK <--> A2A["Typed A2A messages"]
  ADK --> MCP["Authenticated MCP tool gateway"]
  ADK --> PS["Pub/Sub event adapter"]
  MCP --> DET["Deterministic forecast and simulation"]
  MCP --> BQ["BigQuery analytics adapter"]
  ADK --> GEM["Gemini evidence reasoning"]
  ADK --> GMA["Private Gemma policy review"]
  DET --> VX["Vertex supplemental forecast"]
  GW --> AUD["SHA-256 audit and evidence export"]
  OT["OpenTelemetry"] -.-> GW
  SM["Secret Manager / service identity"] -.-> GW
  AR["Artifact Registry"] -.-> UI
  AR -.-> GW
  SAFE["PRODUCTION ACTION: NOT EXECUTED"] --- GW
```

AI Studio is prompt-development tooling, not runtime. Models remain advisory; deterministic gates, workflow state and human authorization are authoritative. No production execution endpoint exists.

## Secure workforce upgrade

The landing route loads independently. Lazy frontend routes call strict FastAPI v1 endpoints. Workforce executions, verification results, role checks and human decisions are persisted and linked to the chained audit log. No layer contains a production execution adapter.

```mermaid
flowchart LR
  L["Landing page"] --> C["Lazy Command Centre"]
  C --> A["Agent Workspaces"]
  A --> API["FastAPI workforce APIs"]
  API --> W["Deterministic workflow services"]
  W --> V["Verification Agent"]
  H["Human actor + server-side access code"] --> R["Role verification + short-lived token"]
  R --> P["Backend approval policy"]
  V --> P
  P --> D["Persisted human decision"]
  D --> E["One-time evidence export"]
  API --> Q["SHA-256 audit chain"]
  P --> Q
```

SentinelOps Nexus is an evidence-driven Enterprise Operational Digital Twin. Its primary path is predictive: observe, correlate, forecast, simulate, compare, explain, and stop for human approval.

## Components

- FastAPI provides validated prediction and simulation contracts.
- The deterministic capacity model creates reproducible seeded forecasts.
- Nine specialised agents expose typed, evidence-linked hand-offs.
- The Digital Twin manifest hashes telemetry and configuration and fixes the seed and network policy.
- The chaos matrix applies identical conditions to Baseline, Fast, Safe, and Optimal strategies.
- Mandatory gates decide eligibility before transparent scoring.
- React presents Time Travel, evidence, agent trace, business impact, tournament, and approval views.
- The inherited reactive investigation workflow remains available as a secondary compatibility path.

No LLM controls state transitions, approval, or production execution. Gemini/ADK/A2A/MCP are integration targets; the current public demo does not falsely claim those optional integrations are active.

See the large Mermaid diagram in the repository README.
