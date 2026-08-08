# Enterprise JSON Calculation Report

## Scope

This correction preserves the existing SentinelOps Nexus technology stack: React, TypeScript, TanStack Query, FastAPI, Pydantic v2, SQLAlchemy/SQLite, the deterministic Digital Twin, the 12-scenario simulator, the FAST/SAFE/OPTIMAL tournament, SHA-256 audit chaining, evidence export, Docker, GitHub Actions, and Google Cloud Run.

**PRODUCTION ACTION: NOT EXECUTED**

## Defects corrected

1. After an upload, the frontend stored the returned backend analysis and then invalidated every query. A second “latest workflow” request could overwrite the selected file's result with an older run.
2. Uploaded telemetry affected the forecast, but the scenario simulator used only bounded control values. Different telemetry files with similar or absent configuration could therefore converge on the same tournament.
3. Approval success was easy to confuse with production execution even though the backend correctly prevented execution.

The frontend now keeps the exact import response active, labels the active source file and workflow ID, and displays the calculated candidate scores. The simulator now anchors uploaded-file scenarios to the latest normalized telemetry saturation. Approval displays a separate recorded-decision state while retaining the mandatory non-execution boundary.

## Supported operational JSON profiles

- Explicit bounded controls
- Flat, nested, or top-level telemetry arrays
- Numeric values encoded as numbers or strings
- CloudWatch parallel metric series
- Prometheus-style timestamp/value series
- Grafana and Datadog nested series exports
- Generic enterprise telemetry containing at least three observations of requests, latency, CPU, memory, queue depth, errors, replicas, or capacity

Missing fields are derived only through documented bounded proxy formulas and are listed in `normalization_notes`. JSON without operational numeric evidence is rejected instead of receiving a fabricated prediction.

## Four supplied control cases

| File | Baseline saturation | FAST | SAFE | OPTIMAL | Recommended |
|---|---:|---:|---:|---:|---|
| `01-baseline-evaluation.json` | 115.6% | 85.3 | 77.2 | 91.0 | OPTIMAL |
| `02-traffic-surge-evaluation.json` | 180.0% | 50.2 | 52.2 | 55.1 | OPTIMAL |
| `03-constrained-dependency-evaluation.json` | 180.0% | 49.6 | 55.9 | 57.8 | OPTIMAL |
| `04-resilient-capacity-evaluation.json` | 18.5% | 83.2 | 87.5 | 87.5 | SAFE |

The 83.2 / 87.5 / 87.5 tournament shown in the reported screenshot is therefore specifically the resilient fourth case. It must not remain visible after another file is successfully analyzed.

## Validation evidence

- Backend: 93 tests passed.
- Operational import suite: 9 tests passed.
- Frontend: 37 tests passed.
- Ruff: passed.
- MyPy: passed across 99 source files.
- Bandit high-severity scan: passed.
- Production frontend build: passed.
- Regression coverage proves that two telemetry files with the same configuration but different observed saturation produce different scenario pressures, tournament signatures, and executive recommendations.

## Approval meaning

`APPROVED — HUMAN DECISION RECORDED` means the authorized human decision is audit-locked and evidence export may proceed. It does not deploy, scale, reconfigure, roll back, call a cloud mutation API, or execute a production command.

**PRODUCTION ACTION: NOT EXECUTED**
