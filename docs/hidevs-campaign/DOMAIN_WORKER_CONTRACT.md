# SentinelOps Reliability Domain Worker

## Purpose

The versioned reliability worker turns operational controls or normalized telemetry into an evidence-linked reliability recommendation. It is a decision-support worker: deterministic systems enforce eligibility, and the workflow stops at a human approval boundary.

## Contract

- Endpoint: `POST /api/v1/domain-workers/reliability-analysis`
- Contract version: `sentinelops.reliability-analysis.v1`
- Strict inputs: unknown fields are rejected.
- Stable output hash: computed from deterministic analysis artifacts, excluding run IDs and timestamps.
- Terminal automated state: `AWAITING_HUMAN`
- Production action: `NOT EXECUTED`

Minimum request:

```json
{
  "contract_version": "sentinelops.reliability-analysis.v1",
  "correlation_id": "review-2026-001",
  "requested_by": "competition-reviewer",
  "name": "Checkout reliability analysis"
}
```

The response contains:

- typed forecast and uncertainty;
- three intervention candidates and every mandatory gate;
- the selected eligible candidate;
- business-impact assumptions and estimate;
- evidence records with SHA-256 content hashes;
- deterministic safety checks;
- audit-chain validity;
- explicit approval requirements; and
- a stable result hash for comparison across runtimes.

## Reproducible commands

```powershell
python scripts/domain_worker_demo.py --preset baseline
python scripts/domain_worker_demo.py --preset surge
python scripts/domain_worker_demo.py --preset resilient
python -m pytest backend/tests/test_domain_worker.py -q
```

## Verified representative results

These values were produced locally on 2026-10-12 from commit `6ff26ab` plus the uncommitted campaign branch changes.

| Preset | Safe-capacity crossing | Customer impact | Confidence | Recommended | Estimated exposure (INR) | Audit | Production action |
|---|---:|---:|---|---|---:|---|---|
| Baseline | +30 min | +45 min | High | OPTIMAL | 14,938,000 | Valid | NOT EXECUTED |
| Surge | 0 min | +45 min | Moderate | OPTIMAL | 147,130,000 | Valid | NOT EXECUTED |
| Resilient | +812 min (outside 45-minute horizon) | +827 min | Moderate | SAFE | 29,626,000 | Valid | NOT EXECUTED |

Stable result hashes:

- Baseline: `7f09ab9b42ac7625c64f795e5bb5d22ca59105d69498fc03405e9e934ff92d46`
- Surge: `2870baa31f90c622b8f43c3652991584e3902d18feb5e3fd1b9a9ffa672c57fb`
- Resilient: `c3cbe847af74911d9362c70acc18fb65b3aac21b70bbeb90e30ca55213c88260`

## Failure behavior

If a stage fails:

1. completed stages and their evidence remain available;
2. the workflow remains in its last valid state;
3. `domain_worker.failed` is appended to the hash-linked audit chain;
4. only the exception type—not the raw exception message—is placed in the audit payload;
5. no production action is executed; and
6. the API returns a bounded conflict response with the workflow ID for inspection.

## Limitations

- The deterministic model is a bounded operational model, not a production control system.
- Commercial exposure is an estimate under explicit assumptions.
- Managed-model reasoning remains advisory and is not required for the deterministic result.
- A valid analysis does not equal a human approval, production deployment, competition validation, points award, or competition award.

