# Existing Repository Opportunity Audit

**Audit date:** 2026-10-12  
**Evidence used:** GitHub repository metadata, recursive Git trees, root agent contracts, and a full local source/test audit of SentinelOps-X.

## Ranked opportunity matrix

| Repository | Eligible track | Potential award | Engineering effort | Evidence needed | Priority |
|---|---|---|---:|---|---:|
| **SentinelOps-X** | Agent Building / Custom Claw Worker | Best Specialized Domain Worker; Best Open Claw Worker Built | Medium | Versioned worker contract, reproducible API demo, tests, audit proof, current deployment evidence | **1** |
| **AI_Reliability_Engineer** | Framework Migration | Best Agent Migration & Technical Comparison | Medium–high | Source/target framework proof, same-case evaluation, measured latency/success/failure recovery | **2** |
| **JALNETRA-AI** | Agent Building | Best Specialized Domain Worker | Medium | Live geospatial evidence, reproducible datasets, test run, passport linkage | **3** |
| **ForgeMind-AI-Rail** | Agent Building or Migration | Best Specialized Domain Worker | Medium–high | Rail-domain evaluation set, deployment proof, safety boundary tests | **4** |
| **KACHRA-OS** | Agent Building | Best Specialized Domain Worker | Medium | Model/data provenance, end-to-end tests, deployment evidence | **5** |
| **chennai-water-bank-ai** | Agent Building or Migration | Best Specialized Domain Worker | Medium | Moss/runtime proof, deterministic scenario evidence, deployment verification | **6** |
| **EndoXAI-RCT** | Agent Building or Migration | Best Specialized Domain Worker | High | Clinical-safety framing, automated tests, model artifact provenance, representative evaluation | **7** |
| **Bottleneck-IQ** | Agent Building | Same categories as SentinelOps-X | Low technically, high eligibility risk | Proof of substantive distinction and organizer duplicate ruling | **Do not submit now** |

## Repository evidence summary

| Repository | Files | Python | TS/TSX | Tests detected | Docs/Markdown | CI workflows | Agent-contract signal |
|---|---:|---:|---:|---:|---:|---:|---|
| SentinelOps-X | 307 | 109 | 34 | 22 | 76 | 2 | `agent.yaml`, `AGENTS.md`, `SOUL.md`, `RULES.md`, `DUTIES.md` |
| Bottleneck-IQ | 321 | 118 | 36 | 25 | 78 | 2 | Agent-related implementation, no root `agent.yaml` at audit time |
| EndoXAI-RCT | 24 | 4 | 0 | 0 | 3 | 0 | `endoxai-rct-review-agent` |
| KACHRA-OS | 92 | 18 | 0 | 8 | 22 | 0 | `kachra-os-waste-intelligence` |
| JALNETRA-AI | 141 | 89 | 0 | 18 | 11 | 1 | `chennai-water-conservation-priority-agent` |
| chennai-water-bank-ai | 106 | 81 | 0 | 16 | 9 | 1 | `chennai-water-bank-ai` |
| ForgeMind-AI-Rail | 192 | 58 | 47 | 9 | 31 | 1 | `forgemind-ai` |
| AI_Reliability_Engineer | 102 | 46 | 10 | 8 | 15 | 1 | `sentinelops-reliability-engineer` |

Counts are structural indicators, not quality scores.

## SentinelOps-X implementation audit

Verified locally:

- Strict Pydantic contracts reject unknown fields.
- Deterministic forecast, bounded Digital Twin, twelve counterfactual scenarios, tournament ranking, and mandatory gates are implemented.
- An ineligible candidate cannot win solely on score.
- The workflow stops at `AWAITING_HUMAN`.
- Approval is role-gated and revalidates workflow state, eligibility, mandatory gates, rationale, audit integrity, and the disabled production boundary.
- Audit events form a SHA-256 chain and exported evidence includes a hash manifest.
- Managed-model output is advisory and fallback status is distinguished from verified managed-runtime calls.
- MCP tools are authenticated and read-only.
- Baseline focused suite before campaign changes: **17 passed**.

Gap selected for implementation:

- The strong internals were fragmented across workflow endpoints. There was no single, versioned, portable domain-worker request/response contract suitable for an external verifier or before/after migration harness.

## Duplicate and overlap risk

The Git trees of SentinelOps-X and Bottleneck-IQ contain **161 identical blobs**, equal to **52.4% of SentinelOps-X's 307 blobs** at audit time. The overlap includes agent runtime, authorization, enterprise contracts, sample evaluations, and infrastructure files.

This does not by itself prove a rules violation, but it creates a material duplicate-submission risk. Treat Bottleneck-IQ as related work and do not submit it as a distinct agent unless the organizer confirms eligibility and the distinct domain behavior is demonstrated.

## Other repository findings

- **EndoXAI-RCT:** strong domain specificity and an explicit human-review description, but no detected automated tests or CI. Medical claims need especially careful evidence and limitations.
- **KACHRA-OS:** useful domain specificity, eight detected tests, extensive docs, but no detected CI or container definition in the recursive tree.
- **JALNETRA-AI:** best secondary domain-worker candidate; 18 detected tests, CI, Docker, and multiple agent-related modules.
- **chennai-water-bank-ai:** solid multi-agent and deterministic framing with 16 detected tests and CI; verify the claimed Moss integration before using it as migration evidence.
- **ForgeMind-AI-Rail:** substantial full-stack footprint and good documentation; needs domain evaluation evidence more than another architecture rewrite.
- **AI_Reliability_Engineer:** narrower and easier to use for a genuine migration comparison than SentinelOps-X; the target framework still requires official track confirmation.

