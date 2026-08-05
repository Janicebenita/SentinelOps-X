# Performance Baseline

Measured locally on 5 August 2026 before the upgrade. Measurements are factual snapshots, not production guarantees.

| Metric | Baseline |
|---|---:|
| JavaScript production asset | 610,943 bytes |
| CSS production asset | 21,144 bytes |
| Initial critical API requests | 5 |
| Python application import/startup | 6,082.84 ms |
| Existing `/health` response | 1,506.39 ms |
| Warm `/api/v1/demo/bootstrap` | 25.17 ms |
| Bootstrap response payload | 19,181 bytes |

Browser FCP and LCP were not reliably measurable in the local CLI environment at audit time and are therefore not fabricated. The observable blockers are the single eager route, eager Recharts dependency, five initial queries, synchronous seeding and an outbound dependency call in `/health`. Render documents a 50-second-or-more wake-up delay on the configured free instance; this infrastructure cold start is distinct from application processing time.
