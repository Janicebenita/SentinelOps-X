"""OpenAI Agents SDK adapter for the SentinelOps reliability worker.

The SDK owns tool routing and execution lifecycle. SentinelOps' deterministic
workflow remains authoritative for evidence, gates, audit state, and the human
approval boundary. This module is installed only with the ``migration`` extra.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from agents import Agent, ModelSettings, RunConfig, RunContextWrapper, Runner, function_tool
from agents.items import ModelResponse
from agents.models.interface import Model
from agents.usage import Usage
from openai.types.responses import ResponseFunctionToolCall
from sqlalchemy.orm import Session

from ..schemas.nexus_contracts import ReliabilityAnalysisResponse, ReliabilityWorkerRequest
from ..services.nexus_workflow import analyze_reliability_worker

MIGRATION_RUNTIME = "openai-agents-sdk"
MIGRATION_AGENT_NAME = "SentinelOps Reliability Orchestrator"
MIGRATION_TOOL_NAME = "analyze_reliability"


@dataclass(frozen=True)
class ReliabilityMigrationContext:
    """Caller-owned resources available to the migrated tool."""

    db: Session


@dataclass(frozen=True)
class MigratedReliabilityRun:
    """Typed result plus framework evidence collected from one SDK run."""

    analysis: ReliabilityAnalysisResponse
    runtime: str
    model_requests: int
    generated_items: int
    tool_name: str


@function_tool(
    name_override=MIGRATION_TOOL_NAME,
    description_override=(
        "Run the deterministic SentinelOps reliability analysis, collect linked evidence, "
        "apply mandatory safety gates, and stop before the required human decision."
    ),
    strict_mode=True,
    failure_error_function=None,
)
def analyze_reliability_tool(
    context: RunContextWrapper[ReliabilityMigrationContext],
    request: ReliabilityWorkerRequest,
) -> str:
    """Invoke the authoritative reliability worker with its versioned request contract."""

    return analyze_reliability_worker(context.context.db, request).model_dump_json()


class DeterministicToolRoutingModel(Model):
    """Offline evaluation model that emits exactly one SDK function-tool call.

    This model is deliberately not represented as a managed LLM. It makes the
    migration testable without credentials while exercising the real SDK Runner,
    strict tool schema, context injection, tool execution, and result lifecycle.
    A managed model can be supplied to :func:`build_reliability_agent` separately.
    """

    def __init__(self, request: ReliabilityWorkerRequest):
        self.request = request
        self.request_count = 0

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        del args, kwargs
        if self.request_count:
            raise RuntimeError("Deterministic routing model received an unexpected second request")
        self.request_count += 1
        request_json = self.request.model_dump(mode="json")
        fingerprint = sha256(
            json.dumps(request_json, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return ModelResponse(
            output=[
                ResponseFunctionToolCall(
                    arguments=json.dumps(
                        {"request": request_json},
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    call_id=f"call_{fingerprint[:24]}",
                    name=MIGRATION_TOOL_NAME,
                    type="function_call",
                    status="completed",
                )
            ],
            usage=Usage(requests=1),
            response_id=f"response_{fingerprint[:24]}",
        )

    async def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        del args, kwargs
        raise NotImplementedError("The deterministic migration evaluator is non-streaming")
        yield  # pragma: no cover - makes this method an async-iterator-compatible generator


def build_reliability_agent(model: str | Model) -> Agent[ReliabilityMigrationContext]:
    """Build the migrated orchestrator around a caller-selected SDK model."""

    return Agent[ReliabilityMigrationContext](
        name=MIGRATION_AGENT_NAME,
        instructions=(
            "Use the analyze_reliability tool exactly once. Treat its evidence, deterministic "
            "gates, and workflow state as authoritative. Never approve, deploy, scale, roll back, "
            "or claim a production action. Return the tool result at the human decision boundary."
        ),
        model=model,
        model_settings=ModelSettings(
            tool_choice=MIGRATION_TOOL_NAME,
            parallel_tool_calls=False,
        ),
        tools=[analyze_reliability_tool],
        tool_use_behavior="stop_on_first_tool",
    )


def run_migrated_reliability_analysis(
    db: Session,
    request: ReliabilityWorkerRequest,
    *,
    model: Model | str | None = None,
) -> MigratedReliabilityRun:
    """Execute the worker through the OpenAI Agents SDK Runner.

    When ``model`` is omitted, the honest offline routing model is used. Supplying
    a model name opts into that provider's configured credentials and transport;
    this repository never silently changes the execution mode.
    """

    selected_model: Model | str = model or DeterministicToolRoutingModel(request)
    agent = build_reliability_agent(selected_model)
    result = Runner.run_sync(
        agent,
        input=request.model_dump_json(),
        context=ReliabilityMigrationContext(db=db),
        max_turns=1,
        run_config=RunConfig(
            tracing_disabled=isinstance(selected_model, DeterministicToolRoutingModel)
        ),
    )
    raw_output = result.final_output
    if isinstance(raw_output, str):
        analysis = ReliabilityAnalysisResponse.model_validate_json(raw_output)
    else:
        analysis = ReliabilityAnalysisResponse.model_validate(raw_output)
    model_requests = (
        selected_model.request_count
        if isinstance(selected_model, DeterministicToolRoutingModel)
        else result.context_wrapper.usage.requests
    )
    return MigratedReliabilityRun(
        analysis=analysis,
        runtime=MIGRATION_RUNTIME,
        model_requests=model_requests,
        generated_items=len(result.new_items),
        tool_name=MIGRATION_TOOL_NAME,
    )
