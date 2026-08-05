from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RoleVerifyRequest(StrictModel):
    actor_name: str = Field(min_length=2, max_length=100)
    access_code: str = Field(min_length=4, max_length=128)


class RoleVerifyResponse(StrictModel):
    verified: bool
    role: Literal["INTERN", "SENIOR_DEVELOPER"]
    permissions: list[str]
    expires_at: datetime
    verification_token: str


class AuthorizedDecision(StrictModel):
    actor_name: str = Field(min_length=2, max_length=100)
    decision: Literal["approve", "reject", "request_more_evidence"]
    rationale: str = Field(min_length=3, max_length=1000)
    verification_token: str = Field(min_length=20)


class AgentActionRequest(StrictModel):
    actor_name: str = Field("human-operator", min_length=2, max_length=100)


class VerificationResult(BaseModel):
    verification_id: int
    workflow_id: int
    subject_type: str
    subject_id: str
    result: Literal["VERIFIED", "REJECTED", "MORE_INFORMATION_REQUIRED"]
    checks: dict[str, bool]
    failed_checks: list[str]
    evidence_ids: list[str]
    reason: str
    verified_at: datetime
    verified_by: str
    audit_event_id: int


class AgentWorkspace(BaseModel):
    agent_name: str
    display_name: str
    purpose: str
    responsibilities: list[str]
    current_status: str
    workflow_id: int | None = None
    last_execution_time: datetime | None = None
    execution_duration_ms: int | None = None
    input_artifact: Any = None
    output_artifact: Any = None
    evidence_references: list[str] = []
    assumptions: list[str] = []
    errors: str | None = None
    retry_count: int = 0
    result_hash: str | None = None
    supported_actions: list[str]
    reasoning_summary: str

