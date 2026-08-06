# Product Requirements Document (PRD): SentinelOps Nexus

> **Submission reference:** This human-authored, architecture-aligned specification is retained as supporting product evidence. Runtime and deployment claims are governed by the repository's [evidence-backed PRD](PRD.md), [compliance matrix](judge-compliance-matrix.md), and [runtime evidence index](runtime-evidence-index.md). Target-state requirements below are not proof that a managed Google Cloud service has run.

**Version:** 1.2  
**Status:** Final Architecture-Aligned Specification  
**Project:** SentinelOps Nexus  
**Date:** August 2026  

---

## 1. Executive Summary
SentinelOps Nexus is an Enterprise Operational Digital Twin for B2B services designed to predict operational bottlenecks before customer impact. The system utilizes deterministic simulation, evidence-grounded AI reasoning, and governed decision support to assist human operators. 

The platform follows a "Zero-Autonomous-Action" policy. It combines deterministic operational models with Google-native AI services to provide foresight while preserving absolute human authority.

**CRITICAL MANDATE:**  
**PRODUCTION ACTION: NOT EXECUTED.**  
Approval records a governed human decision and enables evidence export only. It does not deploy, scale, roll back, reconfigure, or modify production infrastructure.

---

## 2. Problem Statement
Enterprise operations frequently suffer from:
*   **Late Bottleneck Detection:** Issues are identified only after customer impact.
*   **Operational Blind Spots:** Lack of real-time visibility into complex system interdependencies (e.g., Redis saturation).
*   **Delayed Decision Making:** Operators lack the evidence-backed simulations required to make high-stakes changes confidently.
*   **AI Trust Gap:** Need for explainable, policy-verified AI-assisted operations rather than "black box" automation.

---

## 3. Goals & Objectives
*   **Predictive Foresight:** Identify bottlenecks (e.g., Redis saturation) before they breach SLOs.
*   **Deterministic Accuracy:** Run 12+ concurrent "what-if" scenarios to evaluate operational paths.
*   **Explainable Reasoning:** Provide evidence-grounded narratives for every recommendation.
*   **Safety & Governance:** Enforce mandatory human approval and deterministic safety gates.
*   **Auditability:** Maintain a tamper-evident SHA-256-linked audit chain of all events.

---

## 4. Target Users / Stakeholders
*   **Site Reliability Engineers (SREs):** To simulate and verify failover/scaling strategies.
*   **Operations Managers:** To review executive-level briefs and evidence packages.
*   **Compliance Officers:** To audit the decision-making chain and AI reasoning logs.

---

## 5. Functional Requirements

| ID | Requirement | Description | Priority |
|:---|:---|:---|:---|
| **FR-1** | Telemetry Ingestion | Ingestion and validation of real-time enterprise telemetry streams. | P0 |
| **FR-2** | Digital Twin Generation | **Generation of a Digital Twin state from validated telemetry, operational context, and historical analytical data where available.** | P0 |
| **FR-3** | Redis Forecasting | Predictive analysis of Redis saturation and trend forecasting. | P0 |
| **FR-4** | Simulation Engine | Execution of 12 deterministic scenarios (FAST, SAFE, OPTIMAL). | P0 |
| **FR-5** | AI Reasoning | Operational reasoning and synthesis via Gemini Enterprise Agent Platform (formerly Vertex AI). | P1 |
| **FR-6** | Policy Verification | Secondary policy critique and consistency review via Gemma. | P1 |
| **FR-7** | Mandatory Safety Gates | Deterministic logic to block ineligible or unsafe recommendations. | P0 |
| **FR-8** | Human Approval | Mandatory "AWAITING_HUMAN" state requiring manual rationale. | P0 |
| **FR-9** | Audit Chain | Generation of a tamper-evident SHA-256-linked event sequence. | P0 |
| **FR-10** | Evidence Export | Generation of a ZIP package containing simulation results and manifests. | P1 |

---

## 6. Non-Functional Requirements

### 6.1 Performance & Scalability
*   **Stateless Scaling:** Core services are independently packaged for the Cloud Run target architecture.
*   **Asynchronous Processing:** Pub/Sub is the target managed event backbone; the validated local build uses an idempotent in-memory adapter.

### 6.2 Observability Strategy
The system implements a comprehensive observability layer:
*   **Tools:** OpenTelemetry, Cloud Logging, Cloud Monitoring, and Cloud Trace.
*   **Traceability:** End-to-end propagation of Correlation IDs, Trace IDs, and AI Invocation IDs.
*   **Logs:** Structured logs for all agent handoffs, MCP calls, and human decisions.

---

## 7. System Architecture Overview
The system follows a safety-first linear workflow:
1.  **Telemetry Ingestion** → **Redis Forecast Service**
2.  **Digital Twin Engine** → **Simulation Engine** (12 Scenarios)
3.  **Optimization Engine** → **Gemini Enterprise Agent Platform (formerly Vertex AI)**
4.  **Gemma Private Policy Review Engine** → **Mandatory Safety Gates**
5.  **Verification Agent** → **Executive Recommendation Generator**
6.  **AWAITING_HUMAN** → **Human Approval Stage**
7.  **Tamper-Evident Audit Chain** → **Evidence ZIP Generator**

---

## 8. System Components

| Component | Primary Responsibility | Implementation Status |
|:---|:---|:---|
| SentinelOps UI | React-based human-in-the-loop interface. | IMPLEMENTED_AND_VERIFIED |
| Nexus API Gateway | FastAPI gateway with RBAC and JWT validation. | IMPLEMENTED_AND_VERIFIED |
| Google ADK Orchestrator | Coordinates agent lifecycle and A2A communication. | LOCAL_ADAPTER_ONLY |
| MCP Connector Server | Controlled tool gateway for enterprise data. | IMPLEMENTED_AND_VERIFIED |
| Gemini Enterprise Agent Platform | Operational reasoning and synthesis. | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Gemma Policy Engine | Secondary policy critique and review. | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Mandatory Safety Gates | Deterministic override and safety validation. | IMPLEMENTED_AND_VERIFIED |
| BigQuery EDW | Historical and analytical data platform. | ROADMAP_ONLY |
| Pub/Sub Event Bus | Asynchronous event backbone. | LOCAL_ADAPTER_ONLY |

---

## 9. Event Architecture
Pub/Sub serves as the asynchronous backbone for the following event types:
*   **Telemetry events**
*   **Agent task events**
*   **Simulation events**
*   **Verification events**
*   **Workflow events**
*   **Evidence export events**

Pub/Sub provides loose coupling, retry support, and end-to-end traceability through correlation IDs.

---

## 10. Data Requirements

### 10.1 BigQuery Analytical Domains
BigQuery is utilized for historical and analytical persistence across these logical domains:
*   **Historical telemetry**
*   **Forecast analytics**
*   **Simulation results**
*   **Verification results**
*   **Audit exports**
*   **Evidence metadata**

---

## 11. AI System Design
*   **Gemini Enterprise Agent Platform (formerly Vertex AI):** Responsible for evidence-grounded reasoning and executive narratives. Cannot approve or execute actions.
*   **Gemma:** Responsible for private policy critique. Cannot override deterministic safety gates.
*   **Google ADK:** Manages Agent-to-Agent (A2A) communication (Observer, Prediction, Simulation, etc.).

---

## 12. Security Requirements
*   **Authentication:** OAuth2/OIDC-ready with JWT validation.
*   **RBAC:** 
    *   *Intern (0000):* View and simulate only.
    *   *Senior Dev (1111):* May approve with mandatory rationale.
*   **Identity:** Application Default Credentials (ADC) and Cloud Run Service Accounts.
*   **Secrets:** All keys managed via Secret Manager.

---

## 13. Deployment Architecture
The credential-gated target deployment pipeline is prepared as follows:
1.  **Source:** GitHub Repository.
2.  **CI/CD:** GitHub Actions.
3.  **Registry:** Artifact Registry.
4.  **Compute:** Cloud Run.
5.  **Configuration:** Secret Manager, IAM, and Application Default Credentials (ADC).

---

## 14. Traceability Matrix

| Business Requirement | Functional Requirement | Architecture Component | Status |
|:---|:---|:---|:---|
| Bottleneck Detection | FR-3 | Redis Forecast Service | IMPLEMENTED_AND_VERIFIED |
| Operational Twin | FR-2 | Digital Twin Engine | IMPLEMENTED_AND_VERIFIED |
| AI Reasoning | FR-5 | Gemini Enterprise Agent Platform | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Policy Review | FR-6 | Gemma Policy Review Engine | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Event Backbone | FR-1 | Pub/Sub Event Bus | LOCAL_ADAPTER_ONLY |
| Analytical Storage | FR-9 | BigQuery | ROADMAP_ONLY |
| Tool Access | FR-1 | MCP Connector Server | IMPLEMENTED_AND_VERIFIED |
| Agent Coordination | FR-5 | Google ADK Orchestrator | LOCAL_ADAPTER_ONLY |
| Observability | NFR-1 | OpenTelemetry / Cloud Trace | ROADMAP_ONLY |

---

## 15. Risks and Limitations
*   **Cloud Quotas:** **Gemini and Gemma availability depends on the configured Gemini Enterprise Agent Platform (formerly Vertex AI) services and applicable Google Cloud quotas.**
*   **Connectivity:** Requires active connection to Google Cloud for managed services (BigQuery, Pub/Sub).
*   **Local Fallback:** Deterministic local fallback is available for development environments without cloud credentials.
*   **Antigravity:** EXCLUDED_BY_SCOPE.

---

## 16. Acceptance Criteria
*   **AC-1:** System must enter "AWAITING_HUMAN" state after every recommendation.
*   **AC-2:** Mandatory Safety Gates must block recommendations if evidence is incomplete.
*   **AC-3:** Audit chain must produce a valid SHA-256 hash for every human decision.
*   **AC-4:** Gemini structured output must be validated against Pydantic schemas before processing.
*   **AC-5:** Senior Developer approval must fail if the rationale field is empty.
