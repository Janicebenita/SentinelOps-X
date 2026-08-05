# SentinelOps Nexus Release-Candidate Review

Review date: 5 August 2026  
Candidate baseline: `main` after the secure operational-workforce upgrade  
Reviewer role: Principal full-stack, AI systems, security, DevOps, performance and QA review  

## Release recommendation

**RECOMMEND RELEASE**, subject to the normal GitHub `Validate SentinelOps` check completing successfully for the release-candidate commit. No open functional or security release blocker remains. The enforced product boundary remains:

> **PRODUCTION ACTION: NOT EXECUTED**

## Pass/fail checklist

| Release gate | Result | Evidence |
|---|---:|---|
| Every AI Workforce card is clickable | PASS | Frontend test renders all 11 catalogue entries as links to `/agents/:agentName`. |
| Every supported agent action calls the backend | PASS | Frontend Run/Re-run tests assert POST calls; backend test executes run and rerun for all 11 agents. |
| No agent action is frontend-only | PASS | `nexusApi.runAgent` targets persisted workflow APIs; backend creates `AgentExecution` and chained audit events. |
| Verification Agent is operational | PASS | Technical verification endpoint and workforce execution both run the agent. |
| Verification results are persisted | PASS | `VerificationRecord` database assertion passes and result includes its audit event ID. |
| Trial code `0000` maps to Intern | PASS | API and live deployment checks return `INTERN`. |
| Intern cannot approve | PASS | Current and legacy approval APIs return HTTP 403 `APPROVER_NOT_QUALIFIED`. |
| Trial code `1111` maps to Senior Developer | PASS | API and live deployment checks return `SENIOR_DEVELOPER`. |
| Senior approval requires rationale | PASS | Strict request schema returns HTTP 422 when rationale is missing; UI remains disabled without it. |
| Expired role tokens are rejected | PASS | Backend test returns HTTP 401 `ROLE_TOKEN_EXPIRED`. |
| Raw codes absent from application logs | PASS | Release scan of repository `.log` files and captured authentication logs found no raw codes. |
| Raw codes absent from database | PASS | Persisted `RoleVerification` field inspection confirms only a keyed fingerprint is stored. |
| Raw codes absent from API responses | PASS | Role-response assertions confirm neither code is returned; tokens contain no plaintext code. |
| Raw codes absent from audit exports | PASS | Parsed evidence ZIP contains no `access_code` field or quoted trial-code value. |
| Raw codes absent from frontend bundles | PASS | Production `dist` scan for environment names and code-bearing access fields returned no matches. |
| Backend authorization is authoritative | PASS | Both Nexus and compatibility approval routes verify signed tokens, actor identity and role server-side. |
| Landing page loads correctly | PASS | Route test and deployed `/` validation show hero, navigation, capabilities and safety boundary. |
| Command-centre loads correctly | PASS | Deployed `/command-centre` validation and application tests pass. |
| SPA refresh routes work | PASS | Render wildcard rewrite targets `/index.html`; direct deployed route navigation succeeds. |
| Initial load is improved | PASS | Route splitting, deferred chart/evidence data and reduced initial requests are measured below. |
| Evidence export remains valid | PASS | ZIP opens without errors and every `manifest.sha256` entry matches its artifact. |
| Audit-chain verification succeeds | PASS | End-to-end run returns `audit_valid: true`; verification uses the calculated chain result. |
| No production execution endpoint exists | PASS | OpenAPI path scan found no execute/apply/deploy-production endpoint. |
| README matches implementation | PASS | Routes, 11 agents, roles, trial credentials, safety, deployment and performance claims correspond to code and tests. |
| `render.yaml` matches final structure | PASS | Existing API, simulator and static service names are preserved; SPA rewrite, health, caching and server-only role settings are present. |
| Full test and analysis suite passes | PASS | Exact evidence below. |

## Issue found and corrected during RC review

The compatibility endpoint `POST /api/incidents/{iid}/approve` accepted only an operator name. It could not execute a production action, but it did not enforce the new product-wide approver-role policy. The endpoint now requires a signed verification token and rationale, revalidates actor identity, and allows approval only for `SENIOR_DEVELOPER`. Its rejection endpoint also requires a valid signed identity. Regression coverage proves an Intern receives HTTP 403 and a request without rationale receives HTTP 422.

The Verification Agent's `audit_completeness` check previously used a constant true value. It now invokes the real SHA-256 chain verifier and uses that calculated result when deciding `VERIFIED` or `REJECTED`.

## Exact test evidence

### Backend and deterministic workflow

```text
python -m pytest backend/tests demo_app/tests -q
51 passed, 1 third-party deprecation warning in 10.59s

python scripts/nexus_e2e.py
workflow state: DECIDED
scenarios: 12
FAST eligible: false
winner: optimal
audit valid: true
production action: NOT EXECUTED
```

The one warning is emitted by FastAPI's test client compatibility layer and does not affect application behavior.

### Frontend

```text
cd frontend
pnpm test
3 test files passed
12 tests passed

pnpm run build
2252 modules transformed
build completed successfully
```

The frontend tests explicitly cover the landing page, all 11 clickable cards, backend Run/Re-run calls, Intern display/disable behavior, Senior Developer rationale gating, guided demo and the safety boundary.

### Static analysis and security

```text
ruff check backend demo_app scripts
All checks passed

mypy backend demo_app scripts
Success: no issues found in 61 source files

bandit -q -lll -r backend demo_app scripts
Passed

pnpm audit --audit-level high
Passed release threshold; one moderate transitive development-tool advisory remains
```

The production bundle and repository log scans returned no credential-field or raw trial-code match. OpenAPI inspection returned:

```text
production_execution_endpoints: []
```

## Performance evidence

| Measurement | Before | Release candidate |
|---|---:|---:|
| Backend import/startup | 6082.84 ms | 2567.94 ms |
| Warm health request | 1506.39 ms | 123.23 ms |
| Agent catalogue request | not available | 10.09 ms local |
| Critical command-centre requests | 5 | 2 |
| Eager JavaScript | 610.94 KB | approximately 194 KB for landing shell |

Release build chunks include a 3.70 KB landing route, 3.50 KB Agent Workspace route, 3.21 KB approval route and 27.30 KB command-centre application chunk. The 404.26 KB telemetry chart is deferred until needed. Render free-tier wake-up delay is infrastructure cold start and is not included as an application rendering improvement.

## Deployment readiness

The repository is ready for the existing Render Blueprint. `render.yaml` preserves these services:

- `janicebenita-sentinelops-nexus`
- `janicebenita-sentinelops-nexus-api`
- `janicebenita-sentinelops-nexus-simulator`

Release procedure:

```powershell
git push origin main
gh run watch --exit-status
```

Render uses `autoDeployTrigger: checksPass`. If Blueprint configuration changed, open the existing Blueprint, run **Manual sync**, review the diff, approve it, and confirm all three services report **Live** on the release commit. Validate `/`, `/command-centre`, `/agents`, `/api/v1/health`, Intern HTTP 403, Senior approval with rationale, audit verification and one-time evidence export.

## Rollback instructions

Application rollback is non-destructive because SentinelOps does not execute production infrastructure actions.

1. In Render, open each existing service and choose the last known-good deployment.
2. Select **Rollback** for the static frontend, API and simulator deployments.
3. Confirm API health and the visible `PRODUCTION ACTION: NOT EXECUTED` boundary.
4. Revert the release commit in GitHub with a new revert commit; do not rewrite `main` history.
5. Push the revert and wait for GitHub validation before allowing Render's checks-passed deployment.
6. SQLite on Render is ephemeral. Do not treat it as a durable rollback store; use PostgreSQL and migrations for production retention.

Recommended commands:

```powershell
git revert <release-commit-sha>
git push origin main
gh run watch --exit-status
```

## Unresolved risks

- Render free services can sleep and may take approximately 50 seconds or more to wake.
- Render's SQLite database is ephemeral. Managed PostgreSQL is required for durable production records.
- The demonstration access codes are intentionally simple and must be replaced by enterprise SSO, centralized identity and RBAC before production use.
- One moderate transitive frontend development-tool advisory remains below the configured high-severity release threshold; continue dependency monitoring.
- Browser performance varies by device and network. FCP and LCP were not claimed because a repeatable browser-lab measurement was not available in this audit.

None of these risks permits or introduces production execution. SentinelOps Nexus remains a decision-support and evidence-recording product with a mandatory human boundary.
