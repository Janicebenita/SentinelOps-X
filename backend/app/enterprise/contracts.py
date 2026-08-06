from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EventEnvelope(StrictModel):
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    schema_version: Literal["1.0"] = "1.0"
    workflow_id: int
    correlation_id: str
    causation_id: str | None = None
    source_service: str
    event_type: str
    timestamp: datetime = Field(default_factory=utcnow)
    actor: str
    artifact_references: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    retry_count: int = Field(0, ge=0, le=10)
    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    payload: dict[str, Any] = Field(default_factory=dict)


class A2AMessage(StrictModel):
    message_id: str = Field(default_factory=lambda: uuid4().hex)
    workflow_id: int
    task_id: str = Field(default_factory=lambda: uuid4().hex)
    correlation_id: str
    sender: str
    receiver: str
    action: str
    status: Literal["delegated", "running", "completed", "rejected", "retry", "timed_out", "cancelled"] = "delegated"
    input_artifacts: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    error: str | None = None
    retry_count: int = Field(0, ge=0, le=10)
    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime


class ToolCall(StrictModel):
    workflow_id: int
    correlation_id: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class EvidenceReasoningRequest(StrictModel):
    workflow_id: int
    evidence_ids: list[str]
    evidence: list[dict[str, Any]]
    purpose: Literal["correlate", "contradictions", "executive_brief", "missing_evidence", "business_impact"]

class EvidenceReasoningOutput(StrictModel):
    purpose: str
    summary: str
    contradictions: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    evidence_ids: list[str]
    authoritative: Literal[False] = False
    production_action: Literal["NOT_EXECUTED"] = "NOT_EXECUTED"


class PolicyReviewRequest(StrictModel):
    workflow_id: int
    candidate: dict[str, Any]
    deterministic_gates: list[dict[str, Any]]
    evidence_ids: list[str] = Field(default_factory=list)
