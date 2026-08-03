# Final validation report

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
- The React bundle should be code-split in a later performance iteration.
- The TestClient dependency emits a deprecation warning that does not affect runtime behaviour.

## Safety conclusion

The tested approval action records a human decision and permits evidence export. It does not deploy, modify production infrastructure or call production credentials. **PRODUCTION ACTION: NOT EXECUTED.**
