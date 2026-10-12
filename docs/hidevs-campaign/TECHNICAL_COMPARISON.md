# Technical Comparison: Local Adapter vs OpenAI Agents SDK

## Compared implementations

- **Original:** direct invocation of the versioned SentinelOps reliability worker, alongside the repository's metadata-only `local-adk-adapter` orchestration record when Google ADK is unavailable.
- **Migrated:** OpenAI Agents SDK `Agent` + `Runner` + strict `function_tool`, with the same deterministic worker as the authoritative tool.

This is a side-by-side adapter migration. It does not claim that the repository's default deployment has been switched or that Google ADK was previously executing the worker.

## Results summary

| Dimension | Original path | Migrated SDK path | Evidence |
|---|---|---|---|
| Input contract | `ReliabilityWorkerRequest` v1 | Same contract inside strict tool schema | Schema unit test |
| Tool calling | Direct Python call | Real SDK model response, Runner planning, strict argument validation, context injection, tool execution | 4 focused migration tests |
| Task success | 30/30 local evaluation runs | 30/30 local evaluation runs | 3 cases × 10 iterations |
| Behavioral equivalence | Reference result | 30/30 paired result hashes matched | Evaluation script hard-fails on mismatch |
| Safety boundary | `AWAITING_HUMAN` | `AWAITING_HUMAN` | Every evaluated result |
| Production mutation | Disabled | Disabled | Every evaluated result and unit test |
| Audit validity | Valid | Valid | Every evaluated result |
| Failure behavior | Worker records bounded stage failures | SDK surfaces authoritative tool failures; no fabricated result | Worker and migration failure tests |
| Model dependency | None for deterministic path | None in offline evaluator; provider required only when explicitly selected | Execution mode metadata |
| Output rewriting | None | None; `stop_on_first_tool` returns tool output | Agent configuration |
| Direct dependency change | None | One optional direct dependency: `openai-agents` | `pyproject.toml` |

## Tool-calling correctness

The migrated model produces a `ResponseFunctionToolCall` with a unique call ID and the complete versioned request nested under the tool's `request` argument. The SDK—not application code—parses the call against the generated strict JSON schema and injects `ReliabilityMigrationContext` before execution.

The agent exposes only `analyze_reliability`, constrains `tool_choice` to that tool, disables parallel tool calls, permits one turn, and stops on the first tool result. These settings reduce nondeterministic orchestration behavior while preserving a real SDK execution path.

## Task success and output quality

For baseline, surge, and resilient cases, all 30 paired runs completed successfully. Every migrated output matched its native counterpart's stable result hash and retained:

- forecast and uncertainty;
- all intervention candidates and gates;
- the recommended eligible candidate;
- business-impact estimate and disclaimer;
- evidence links and hashes;
- audit validity; and
- the human-approval boundary.

Because the offline router is deterministic, these measurements establish adapter correctness—not general language-model reasoning quality.

## Failure recovery

The authoritative worker already commits each completed stage and appends a bounded `domain_worker.failed` audit event when a later stage fails. The SDK adapter sets `failure_error_function=None`, so the framework does not turn a tool exception into a friendly but misleading success string. The focused failure test confirms that the SDK surfaces the wrapped authoritative error and produces no fabricated analysis.

## Latency

Median local latency increased modestly in this small sample:

| Case | Native median | SDK median | Median difference |
|---|---:|---:|---:|
| Baseline | 77.348 ms | 79.198 ms | +1.850 ms |
| Surge | 73.173 ms | 81.405 ms | +8.232 ms |
| Resilient | 75.600 ms | 80.135 ms | +4.535 ms |

The sample includes only ten iterations per case on one Windows machine. Maximum values were affected by cold local work, so these numbers are reproducibility evidence, not production benchmarks or service-level guarantees.

## Dependency complexity

The original deterministic path stays dependency-neutral. The migrated path adds `openai-agents>=0.23,<0.24` as an optional extra, keeping the default production install unchanged. The SDK brings transitive provider, tracing, schema, and transport dependencies; teams must include those in supply-chain and deployment review.

## Maintainability

The adapter reuses the existing request/response models and authoritative workflow instead of duplicating domain logic. Framework-specific code is isolated under `backend/app/migrations`. Tests compare stable hashes rather than brittle textual output.

The principal maintenance cost is SDK API compatibility. The version is bounded to the tested minor line, and upgrades should rerun the strict-schema, failure, full-suite, and three-case equivalence checks.

## Deployment requirements

| Mode | Credentials | Network | Intended use |
|---|---|---|---|
| Native deterministic | None | None | Default worker and API |
| SDK offline evaluator | None | None | Reproducible migration verification |
| SDK managed model | Provider-specific | Yes | Explicit opt-in after security/cost review |

## Compatibility limitations

- The current wrapper is synchronous.
- Managed-model tool selection, latency, token usage, and cost are unavailable because no provider call was run.
- Only the reliability worker has been migrated.
- The optional adapter is not wired into the default FastAPI route or deployed service.
- Competition validation, points, or award eligibility remain unverified until the organizer confirms the live rules and accepts the submission.
