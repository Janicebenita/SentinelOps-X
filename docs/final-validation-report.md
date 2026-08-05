# Final validation report

## 6 August 2026 exact-specification validation

The final conformance pass introduced the explicit `AWAITING_HUMAN` workflow state, backend-populated evidence/audit/verification routes, calculated approver qualification including mandatory rationale, and the required `agent.opened`, `approval.enabled`, `approval.submitted`, `rejection.submitted` and `more_evidence.requested` audit events. The Verification Agent persists `MORE_INFORMATION_REQUIRED` after role verification when rationale is still absent and persists `VERIFIED` only when the submitted decision passes every qualification check.

Final exact results: **52 backend/demo tests passed**, **13 frontend tests passed**, Ruff passed, MyPy passed across 61 files, Bandit passed, production build passed, compiled credential scan passed, audit chain passed, and all evidence manifest hashes passed.

## 5 August 2026 secure workforce upgrade

Implemented route-split landing and command-centre experiences; eleven clickable operational Agent Workspaces; persisted AgentExecution, RoleVerification, HumanDecision and VerificationRecord models; a technical and qualification Verification Agent; signed short-lived role tokens; Intern blocking; Senior Developer approval with rationale; lightweight health/readiness separation; deferred non-critical frontend work; expanded CI, Docker and Render configuration.

Files created include `backend/app/auth/roles.py`, `backend/app/services/workforce.py`, `backend/app/schemas/upgrade_contracts.py`, `backend/Dockerfile`, routed frontend pages/components, upgrade tests and the audit/performance/RBAC/workforce/making-of documents. Existing workflow, audit, evidence and one-time export services were modified without adding any production execution adapter.

Database migration status: four additive tables are created by SQLAlchemy metadata on application lifespan. Existing SQLite Nexus tables remain compatible; no destructive migration or data rewrite occurs. Render SQLite remains ephemeral.

New API routes: global agent catalogue/detail/status; workflow agent detail/run/rerun/events; role verification; workflow verification run/results; token-authorized approve/reject/request-evidence. New frontend routes are documented in README.

Validation results:

- Python: 52 tests passed (backend plus demo app).
- Ruff: passed.
- MyPy: passed across 61 source files.
- Bandit high-severity scan: passed.
- Frontend: 13 tests passed.
- TypeScript/Vite production build: passed.
- E2E: Intern 403, Senior Developer approval, audit valid, ZIP hashes valid, production action not executed.
- Workforce: all 11 agents listed, opened, run and rerun; 22 executions persisted in test.
- Security: invalid and expired credentials rejected; plaintext codes absent from responses/persistence; no production execution endpoint.
- Dependency scanning: Pytest was raised to `>=9.0.3` after CI identified `PYSEC-2026-1845` in the previous development-only 8.x line.
- Frontend dependency scanning: Vite was raised to 6.4.3 and Vitest to 3.2.6 after CI identified patched high/critical advisories in the previous toolchain. The high-severity audit now passes; one moderate development-tree advisory remains reported.

Performance: startup 6,082.84 → 2,567.94 ms; health 1,506.39 → 123.23 ms; agent list 10.09 ms; initial landing assets approximately 193 KB raw instead of a 610,943-byte eager application asset; command-centre critical API requests 5 → 2. See `performance-after.md` for measurement boundaries.

Exact commands:

```powershell
python -m pytest backend/tests demo_app/tests -q
ruff check backend demo_app scripts
mypy backend demo_app scripts
bandit -q -lll -r backend demo_app scripts
python scripts/nexus_e2e.py
cd frontend
pnpm test
pnpm run build
```

Known limitations: demo access codes are not enterprise identity; Render free-tier cold starts remain; Render SQLite is ephemeral; FCP/LCP were not fabricated without a controlled Lighthouse environment; deterministic calculations are bounded operational estimates.

---

Date: 3 August 2026  
Branch: `codex/add-render-live-links`

## Validated working scope

- Persisted versioned Nexus workflow and backend-owned state transitions
- Five-point seeded Payment Service and Redis telemetry
- Transparent bounded linear saturation forecast
- Immutable hashed Twin manifest and same-seed replay
- Twelve deterministic scenarios
- FAST, SAFE and OPTIMAL intervention tournament
- Mandatory failover-gate disqualification of FAST
- Transparent business-impact equations and assumptions
- Evidence-linked executive brief
- Explicit human decision before evidence export
- Chained SHA-256 audit verification and ZIP artifact hashes
- React command centre backed by persisted API data
- One-click six-stop Guided Demo with pause and manual navigation
- Explore Mode presets, bounded reruns and selectable scenario inspection
- 4:50 narrated 1080p H.264/AAC synchronized simulation with captions
- No production execution route

## Commands and exact results

### Backend and demo tests

```powershell
python -m pytest backend\tests demo_app\tests -q
```

Result: **41 passed**, one Starlette TestClient deprecation warning, zero failures.

### Ruff

```powershell
python -m ruff check backend demo_app scripts
```

Result: **All checks passed**.

### MyPy

```powershell
python -m mypy backend demo_app scripts
```

Result: **Success: no issues found in 56 source files**.

### Bandit

```powershell
python -m bandit -q -lll -r backend demo_app scripts
```

Result: exit code 0; no high-severity findings reported.

### Frontend tests

```powershell
pnpm test
```

Result: **2 test files passed, 5 tests passed**. Guided Demo is explicitly tested not to call approval.

### Frontend production build

```powershell
pnpm run build
```

Result: **passed**, 2,428 modules transformed. Vite reported a non-blocking 607.41 KB chunk-size warning.

### Narrated demo media

Result: **passed** — duration 4:50.03; 1920×1080 H.264 High profile at 30 fps; one AAC-LC 48 kHz stereo narration stream; synchronized SRT captions. All nine scene midpoints and the final seconds were visually inspected. Measured integrated loudness is -14.7 LUFS, loudness range is 3.0 LU, and true peak is -3.4 dBFS. The closing card holds through “Thank you” and displays **PRODUCTION ACTION: NOT EXECUTED**.

### Seeded end-to-end workflow

```powershell
python scripts\nexus_e2e.py
```

Result:

```text
state=DECIDED
scenarios=12
fast_eligible=False
winner=optimal
audit_valid=True
production_action=NOT EXECUTED
```

The script also opens the exported ZIP and verifies every `manifest.sha256` entry.

### Backend startup

The API was started locally with Uvicorn on port 8020 and queried directly.

```json
{"status":"ok","service":"sentinelops-nexus-api","production_action":"NOT EXECUTED"}
{"ready":true,"database":true,"provider":"deterministic","production_action":"NOT EXECUTED"}
```

## Honest limitations

- The working demo uses seeded telemetry rather than live enterprise systems.
- The forecast is deterministic and transparent but not a calibrated probability.
- The Digital Twin is bounded by documented variables and assumptions.
- Business-impact outputs are operational estimates, not accounting results.
- Google ADK, A2A, MCP, Vertex AI and other enterprise-scale components belong to the continued-research architecture unless separately implemented and tested.
- The React bundle is route-split; the heavy telemetry chart and non-critical resource views load after the initial shell.
- The TestClient dependency emits a deprecation warning that does not affect runtime behaviour.

## Safety conclusion

The tested approval action records a human decision and permits evidence export. It does not deploy, modify production infrastructure or call production credentials. **PRODUCTION ACTION: NOT EXECUTED.**
