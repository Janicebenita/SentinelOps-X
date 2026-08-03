# Technical Q&A

- **Is this just a coding assistant?** No. It owns a persisted incident lifecycle, gathers evidence, runs experiments, applies deterministic gates, and requests approval.
- **Why is it agentic?** It selects and executes bounded tools across observation, hypothesis, reproduction, repair and verification states.
- **Why is mock mode acceptable?** It makes judging deterministic and key-free while exercising the real state machine, tests, sandbox and policy.
- **What executes for real?** The failing API, telemetry, regression, copied workspace patch, tests, lint, type and security gates.
- **What is simulated?** The default PR is a local record and incidents 2–3 abstain after diagnosis.
- **How is unsafe code contained?** Network-disabled Docker or an allowlisted temporary Local Sandbox.
- **Why not auto-deploy?** Reliability changes require accountable human control and rollback ownership.
- **How do you prevent false fixes?** Reproduce first, require a failing regression before and passing regression after, then run mandatory gates.
- **Business value?** Lower triage time and toil without surrendering change control.
- **How would this scale?** Queue-backed workers, PostgreSQL, object telemetry stores, and ephemeral sandbox jobs.
- **Why one fully repairable incident?** The MVP prioritizes one credible end-to-end proof over shallow templates.
- **What data is required?** Scoped logs, metrics, traces, repository history and tests.
- **How are credentials protected?** Environment-only configuration, redacted provider errors, no sandbox secrets, and ignored `.env` files.
# Finale judge Q&A

**What is novel?** SentinelOps evaluates several plausible repairs inside one immutable incident twin, then uses counterfactual replay and deterministic eligibility to detect false fixes before human approval.

**Why are multiple candidates safer?** A single generated patch can pass the original regression while masking a symptom. The tournament makes alternatives, risks, failed gates, and nearby behavior directly comparable.

**Is blast radius proven?** No. It is a transparent 0–100 estimate from modified components, transitive dependencies, uncovered critical paths, public contracts, and configuration scope. Assumptions and evidence remain visible.

**Is causal confidence a probability?** No. Low/Moderate/High labels summarize evidence and falsification results; they are not calibrated probabilities.

**Can the model approve or deploy?** No. Backend state policy requires a human approval record, and the product has no automatic deployment route.

**Is the audit package blockchain?** No. It is a SHA-256 tamper-evident event chain and artifact bundle. It does not claim legal non-repudiation.
