# Runtime Evidence Index

Evidence snapshot: 2026-08-06  
Code baseline: `d4a8f8d` (implementation) and `6862f12` (CI evidence documentation)  
Target project: `sentinelops-nexus-finale`  
Target region: `asia-south1`

This index distinguishes tested local behavior from authenticated Google Cloud evidence. A source file or deployment manifest is not proof that a managed service ran.

Current release-candidate local validation: 74 Python tests passed, 14 frontend
tests passed, the TypeScript/Vite production build passed, Ruff passed, MyPy
passed for 95 source files, Bandit reported no high-severity finding, and the
canonical E2E returned workflow `1`, 12 scenarios, FAST ineligible, OPTIMAL
selected, valid audit chain, and `PRODUCTION ACTION: NOT EXECUTED`.

| Capability | Local/CI evidence | Cloud evidence | Status |
|---|---|---|---|
| Deterministic workflow | GitHub Actions run `31071715878`; backend, frontend and E2E jobs passed | Render smoke evidence documented in the final report | IMPLEMENTED_AND_VERIFIED |
| Gemini core reasoning | Provider, strict schema, evidence-reference, authority and fallback tests | No authenticated model invocation ID captured | IMPLEMENTED |
| Gemma policy review | Private-service contract and deterministic non-override tests | No managed/private model revision URL captured | IMPLEMENTED |
| Google AI Studio | Thirteen task-level CRISPE prompts, compiled schema, and contract tests | No AI Studio session/export evidence | IMPLEMENTED |
| Antigravity | Typed read-only provider/status boundary and deterministic fallback | Official participant docs, SDK, endpoint, and access unavailable | BLOCKED_BY_PARTICIPANT_ACCESS |
| Google ADK | Registry, session and orchestration adapter tests | Official ADK package/runtime unavailable in validated environment | LOCAL_ADAPTER_ONLY |
| A2A | Typed, persisted, correlated and trace-propagated handoff tests | No managed A2A service required | IMPLEMENTED_AND_VERIFIED |
| MCP | Authenticated read-only tool gateway and no-mutation tests | No deployed MCP Cloud Run URL | IMPLEMENTED_AND_VERIFIED |
| Managed forecast | Deterministic authoritative fallback and supplemental boundary | No Gemini Enterprise Agent Platform invocation | LOCAL_FALLBACK_AVAILABLE |
| BigQuery | Nine physical partitioned/clustered DDL files plus credentialed provision/write/read tooling | No dataset row/query job ID | IMPLEMENTED |
| Pub/Sub | Typed idempotent adapter plus provisioning and publish/consume smoke tooling | No managed publish/consume message ID | IMPLEMENTED |
| Cloud Run | Images/manifests and CI container builds | No `run.app` URL, revision, IAM or health evidence | IMPLEMENTED |
| OpenTelemetry | Local trace IDs propagate through enterprise adapters | No Cloud Trace span ID | LOCAL_ADAPTER_ONLY |
| JWT/RBAC | Short-lived signed JWT and approval authority tests | Live Render Intern/Senior probes documented | IMPLEMENTED_AND_VERIFIED for demo JWT; OIDC is LOCAL_ADAPTER_ONLY |
| Audit and Evidence ZIP | Hash-chain and archive validation tests; live Render probe | No Google-managed storage evidence | IMPLEMENTED_AND_VERIFIED |

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

Record successful Cloud Run URLs, revisions, trace IDs, BigQuery job IDs, Pub/Sub message IDs, and model invocation metadata here only after those commands succeed. No such authenticated evidence was available during this snapshot.

## Permanent safety boundary

`PRODUCTION ACTION: NOT EXECUTED`

Cloud scripts provision analytical and hosting boundaries only. They do not add any production remediation endpoint.
