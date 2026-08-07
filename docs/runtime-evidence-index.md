# Runtime Evidence Index

Evidence snapshot: 2026-08-07

Code baseline: `fa3345c` (reconciled local release candidate) and authenticated Google Cloud workflow `31140376799`

Target project: `sentinelops-nexus-finale`  
Target region: `asia-south1`

This index distinguishes tested local behavior from authenticated Google Cloud evidence. A source file or deployment manifest is not proof that a managed service ran.

Current release-candidate local validation: 83 Python tests passed, 32 frontend
tests passed, the TypeScript/Vite production build passed, Ruff passed, MyPy
passed for 98 source files, Bandit reported no high-severity finding, and the
canonical E2E returned workflow `1`, 12 scenarios, FAST ineligible, OPTIMAL
selected, valid audit chain, and `PRODUCTION ACTION: NOT EXECUTED`.

| Capability | Local/CI evidence | Cloud evidence | Status |
|---|---|---|---|
| Deterministic workflow | GitHub Actions run `31071715878`; backend, frontend and E2E jobs passed | Render smoke evidence documented in the final report | IMPLEMENTED_AND_VERIFIED |
| Gemini core reasoning | Provider, strict schema, evidence-reference, authority and fallback tests | No authenticated managed-model invocation ID is claimed | IMPLEMENTED_REQUIRES_RUNTIME_EVIDENCE |
| Gemma policy review | Private-service contract and deterministic non-override tests | Cloud Run service is healthy; managed model invocation/revision evidence is not claimed | RUNTIME_EVIDENCE_REQUIRED |
| Google AI Studio | Thirteen task-level CRISPE prompts, compiled schema, and contract tests | No authenticated AI Studio session/export artifact is claimed | IMPLEMENTED_REQUIRES_RUNTIME_EVIDENCE |
| Antigravity | Typed read-only provider/status boundary and deterministic fallback | Official participant docs, SDK, endpoint, and access unavailable | BLOCKED_BY_PARTICIPANT_ACCESS |
| Google ADK | Registry, session and orchestration adapter tests | Official ADK package/runtime unavailable in validated environment | LOCAL_ADAPTER_ONLY |
| A2A | Typed, persisted, correlated and trace-propagated handoff tests | No separate managed A2A service is required for this boundary | IMPLEMENTED_AND_VERIFIED |
| MCP | Authenticated controlled-tool gateway and no-infrastructure-mutation tests | MCP Cloud Run service passed health and readiness checks in workflow `31140376799` | IMPLEMENTED_AND_VERIFIED_LIVE |
| Managed forecast | Deterministic authoritative fallback and supplemental boundary | No managed supplemental-forecast invocation is claimed | LOCAL_FALLBACK_AVAILABLE |
| BigQuery | Nine physical partitioned/clustered DDL files plus credentialed provision/write/read tooling | Workflow `31140376799` inserted row `smoke-c5c11478-5b8d-43c2-bee5-e3223e000bac` and read it with query job `sentinelops_smoke_85ef5547783b49249e05043d42800030` | IMPLEMENTED_AND_VERIFIED_LIVE |
| Pub/Sub | Typed idempotent adapter plus provisioning and publish/consume smoke tooling | Workflow `31140376799` published, received, and acknowledged message `20178966799882394` | IMPLEMENTED_AND_VERIFIED_LIVE |
| Cloud Run | Images/manifests, nine local image builds, and container health/readiness validation | Nine live services passed authenticated health/readiness checks in workflow `31140376799` | IMPLEMENTED_AND_VERIFIED_LIVE |
| OpenTelemetry | Local trace IDs propagate through enterprise adapters | No exported Cloud Trace ID is claimed | IMPLEMENTED_AND_VERIFIED_LOCAL |
| JWT/RBAC | Short-lived signed JWT and approval authority tests | Live Render Intern/Senior probes documented | IMPLEMENTED_AND_VERIFIED for demo JWT; OIDC is LOCAL_ADAPTER_ONLY |
| Audit and Evidence ZIP | Hash-chain, archive, and `manifest.sha256` validation tests; governed export boundary | Google-managed object storage is not required or claimed | IMPLEMENTED_AND_VERIFIED |

## Reproducible evidence commands

```bash
pytest backend/tests demo_app/tests -q
ruff check backend demo_app scripts
mypy backend demo_app scripts
bandit -q -lll -r backend demo_app scripts
cd frontend && pnpm test && pnpm run build
```

Controlled cloud evidence is collected only after Workload Identity Federation authentication:

```bash
PROJECT_ID=sentinelops-nexus-finale REGION=asia-south1 bash scripts/verify_google_cloud.sh
```

Record managed-model invocation metadata and exported Cloud Trace IDs here only after authenticated checks succeed. Cloud Run health/readiness, BigQuery write/read, and Pub/Sub publish/receive/acknowledge are evidenced by workflow `31140376799`; those results do not prove Gemini, Gemma, Cloud Monitoring, or Cloud Trace runtime execution.

## Permanent safety boundary

`PRODUCTION ACTION: NOT EXECUTED`

Cloud scripts provision analytical and hosting boundaries only. They do not add any production remediation endpoint.
