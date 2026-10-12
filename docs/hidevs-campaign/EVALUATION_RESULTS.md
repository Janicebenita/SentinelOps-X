# OpenAI Agents SDK Migration Evaluation Results

## Status

- Evaluation date: 2026-10-12
- Repository base revision: `6ff26ab` plus local campaign branch changes
- Python: 3.12.14
- Platform: Windows 11 (`10.0.26200`)
- OpenAI Agents SDK: 0.23.1
- Iterations: 10 per case per implementation
- Managed-model run: **NOT RUN — no provider credentials used**
- Execution mode: `offline-deterministic-tool-routing`

## Method

For each case, the evaluator:

1. creates an identical `ReliabilityWorkerRequest`;
2. runs the native worker in a fresh in-memory SQLite database;
3. runs the SDK adapter in another fresh in-memory database;
4. measures worker execution time with `time.perf_counter`;
5. compares stable result hashes; and
6. verifies the migrated terminal state, production boundary, and audit status.

Command:

```bash
python scripts/migration_evaluation.py --iterations 10
```

The script exits non-zero on any hash mismatch.

## Correctness

| Case | Paired runs | Hash matches | State | Audit | Production action | Recommended candidate |
|---|---:|---:|---|---|---|---|
| Baseline | 10 | 10 | `AWAITING_HUMAN` | Valid | NOT EXECUTED | OPTIMAL |
| Surge | 10 | 10 | `AWAITING_HUMAN` | Valid | NOT EXECUTED | OPTIMAL |
| Resilient | 10 | 10 | `AWAITING_HUMAN` | Valid | NOT EXECUTED | SAFE |

Task success was 30/30 for the native path and 30/30 for the migrated path. Behavioral equivalence was 30/30 by paired stable-result hash.

Measured hashes for these evaluation inputs:

- Baseline: `3b7ea47fdc7cfbb614a442cbe07f67fcaf8f8ded6cae3473710f7dcdc430e2d6`
- Surge: `0f68fdae493018db66f2abd0187ec1c6212099bb32fc0b0202355e47d1e72adf`
- Resilient: `528c89dc286c01e01bec4e0993a63e3580e65b5fb1b9d4a54171b0058c8b7aa6`

These differ from the standalone demo hashes because the evaluation uses distinct `source_label` values. Within each paired native/migrated request, the hashes match.

## Latency

| Case | Path | Median | P95* | Min | Max |
|---|---|---:|---:|---:|---:|
| Baseline | Native | 77.348 ms | 664.143 ms | 73.232 ms | 664.143 ms |
| Baseline | SDK | 79.198 ms | 215.352 ms | 75.166 ms | 215.352 ms |
| Surge | Native | 73.173 ms | 87.515 ms | 70.616 ms | 87.515 ms |
| Surge | SDK | 81.405 ms | 88.975 ms | 77.447 ms | 88.975 ms |
| Resilient | Native | 75.600 ms | 190.065 ms | 72.042 ms | 190.065 ms |
| Resilient | SDK | 80.135 ms | 82.709 ms | 74.175 ms | 82.709 ms |

\* P95 uses the nearest-rank observation; with ten samples it is the maximum. Cold local work produced visible outliers. Do not treat these figures as a production benchmark.

## Focused test results

```text
4 passed in 2.82s
```

The focused tests verify:

- real SDK Runner and strict function-tool execution;
- one model request and one tool call;
- strict schema reuse;
- deterministic-result equivalence;
- preservation of the human and production boundaries; and
- authoritative failure propagation.

## Unavailable measurements

The following are deliberately reported as unavailable:

- managed-model task success;
- model-provider latency;
- token usage and cost;
- provider retry behavior;
- deployed service throughput; and
- competition judge outcome.

No value in this document is an award, production-adoption claim, or claim of competition validation.
