# SentinelOps OpenAI Agents SDK Migration Guide

## Scope

This migration moves the **reliability-orchestration boundary** from the repository's `local-adk-adapter` path to an optional OpenAI Agents SDK adapter. It does not replace the deterministic forecast, Digital Twin, scenario engine, safety gates, audit chain, or human-decision service.

The target is a genuine framework integration:

1. an SDK `Agent` defines the migrated orchestrator;
2. an SDK `Model` emits the tool call;
3. the SDK `Runner` validates and executes that call;
4. an SDK `function_tool` injects caller-owned database context and invokes the versioned worker contract; and
5. `stop_on_first_tool` returns the authoritative tool result without an LLM rewriting it.

The implementation follows the official [OpenAI Agents SDK guide](https://developers.openai.com/api/docs/guides/agents/sdk) and [agent-building guide](https://developers.openai.com/api/docs/guides/agents/quickstart?lang=python). No competition rule is assumed to require this specific framework.

## Before and after

```text
Before
API/workforce -> local-adk-adapter metadata -> deterministic workflow

Migrated path
ReliabilityWorkerRequest
  -> OpenAI Agents SDK Agent
  -> Runner
  -> strict analyze_reliability function tool
  -> deterministic workflow
  -> ReliabilityAnalysisResponse
  -> AWAITING_HUMAN
```

Both paths use `sentinelops.reliability-analysis.v1`. Result hashes exclude workflow IDs and timestamps, allowing behavior to be compared without collapsing separate audit records.

## Files

- `backend/app/migrations/openai_agents_reliability.py` — SDK agent, strict tool, context, offline routing model, and execution adapter.
- `backend/tests/test_openai_agents_migration.py` — strict-schema, equivalence, safety-boundary, and failure-propagation tests.
- `scripts/migration_evaluation.py` — same-case native-versus-migrated evaluation.
- `pyproject.toml` — isolated `migration` optional dependency.

## Install

Use Python 3.11 or newer from the repository root:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev,migration]"
```

On macOS or Linux, use `.venv/bin/python` in place of `.venv/Scripts/python`.

## Run the focused migration tests

```bash
python -m pytest backend/tests/test_openai_agents_migration.py -q
```

Expected behavior:

- one SDK model request and one strict function-tool invocation;
- a typed reliability response;
- terminal state `AWAITING_HUMAN`;
- `production_action: NOT EXECUTED`;
- a valid audit chain; and
- the same deterministic result hash as the native path for the same request.

## Reproduce the comparison

```bash
python scripts/migration_evaluation.py --iterations 10
```

The evaluator runs baseline, surge, and resilient cases through both paths using new in-memory databases. It exits with an error if any paired result hash differs.

The default evaluation model is `DeterministicToolRoutingModel`. It emits one real SDK function-tool call and uses no provider credentials. This validates framework wiring and behavioral preservation, but it is **not** a managed-model quality evaluation.

## Opt into a configured managed model

Application code may pass a model name or an SDK `Model` instance:

```python
result = run_migrated_reliability_analysis(
    db,
    request,
    model="your-configured-model",
)
```

This is an explicit mode change. The caller is responsible for provider configuration, credentials, data-handling review, tracing policy, cost controls, and model availability. This campaign did not run or claim managed-model measurements.

## Safety invariants preserved

- The tool contract rejects unknown fields.
- The model cannot modify deterministic gates or eligibility.
- Only one tool is exposed and tool choice is constrained to it.
- Parallel tool calls are disabled.
- Raw tool output is returned without a second model rewrite.
- Failures are surfaced; no synthetic success is produced.
- The authoritative workflow stops at `AWAITING_HUMAN`.
- Production mutation remains disabled.

## Rollback

The migration is additive. Remove the optional extra from the installation and continue calling `analyze_reliability_worker` or the existing FastAPI endpoint. No data migration or schema rollback is required.

## Known limitations

- The adapter currently exposes synchronous `Runner.run_sync`; async server integration should use the SDK's async runner instead of calling this function inside an active event loop.
- Managed-model task success, latency, token usage, and cost were not measured.
- The adapter migrates one specialized reliability worker, not all eleven SentinelOps workforce entries.
- OpenAI Agents SDK is optional and version-bounded to the tested `0.23.x` line.
