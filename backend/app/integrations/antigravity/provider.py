"""Truthful Antigravity provider boundary.

No official runtime call is attempted until participant access and an endpoint
are explicitly configured. This prevents a compatibility adapter from being
misreported as managed-runtime evidence.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from ...config import settings


class AntigravityStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    integration: Literal["antigravity"] = "antigravity"
    status: Literal["DOCUMENTATION_OR_ACCESS_BLOCKED", "IMPLEMENTED_REQUIRES_CREDENTIALS"]
    configured: bool
    provider: Literal["official-antigravity-unavailable"] = "official-antigravity-unavailable"
    sdk_runtime_version: None = None
    last_invocation: None = None
    latency_ms: None = None
    workflow_id: None = None
    trace_id: None = None
    fallback_state: Literal["DETERMINISTIC_LOCAL_SIMULATION"] = "DETERMINISTIC_LOCAL_SIMULATION"
    error: str
    evidence_id: Literal["docs/antigravity-integration.md"] = "docs/antigravity-integration.md"
    official_runtime_invoked: bool = False
    participant_access: bool
    endpoint_configured: bool
    blocker: str
    production_action: Literal["NOT_EXECUTED"] = "NOT_EXECUTED"


def get_antigravity_status() -> AntigravityStatus:
    access = settings.antigravity_participant_access
    endpoint = bool(settings.antigravity_endpoint.strip())
    configured = access and endpoint
    return AntigravityStatus(
        status="IMPLEMENTED_REQUIRES_CREDENTIALS" if configured else "DOCUMENTATION_OR_ACCESS_BLOCKED",
        configured=configured,
        participant_access=access,
        endpoint_configured=endpoint,
        blocker=(
            "Authenticated runtime smoke test is required before this integration can be verified."
            if configured
            else "Official participant documentation or runtime access is not available in this environment."
        ),
        error=(
            "Runtime invocation has not been authenticated."
            if configured
            else "Official participant documentation, SDK, endpoint, or access is unavailable."
        ),
    )
