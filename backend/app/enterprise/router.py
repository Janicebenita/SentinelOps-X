from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import A2AMessageRecord, NexusEvidence, NexusRun
from ..integrations.antigravity import AntigravityStatus, get_antigravity_status
from .contracts import A2AMessage, EventEnvelope, EvidenceReasoningRequest, PolicyReviewRequest, ToolCall, utcnow
from .runtime import event_bus, integration_health, persist_a2a, reason_with_gemini, review_with_gemma, supplemental_forecast

router = APIRouter(prefix="/api/v1/platform", tags=["Google-native platform"])
Db = Annotated[Session, Depends(get_db)]
TOOLS = {"get_telemetry", "get_latest_metrics", "get_service_topology", "get_slo_configuration", "get_incident_history",
    "get_evidence", "create_twin_manifest", "run_scenario", "get_scenario_result", "get_tournament_results",
    "get_gate_results", "calculate_business_impact", "export_evidence_package"}


def authorize(value: str | None) -> None:
    if not value or value.removeprefix("Bearer ") != settings.integration_token:
        raise HTTPException(401, "Authenticated integration token required")


@router.get("/integrations")
def integrations(db: Db) -> Any: return integration_health(db)


@router.get("/integrations/antigravity/status", response_model=AntigravityStatus)
def antigravity_status() -> AntigravityStatus:
    return get_antigravity_status()


@router.post("/events/publish")
def publish(event: EventEnvelope, authorization: Annotated[str | None, Header()] = None) -> Any:
    authorize(authorization); return event_bus.publish(event)


@router.post("/a2a/messages")
def send_a2a(message: A2AMessage, db: Db, authorization: Annotated[str | None, Header()] = None) -> Any:
    authorize(authorization)
    row = persist_a2a(db, message)
    return {"message_id": row.message_id, "status": row.status, "trace_id": row.trace_id, "production_action": "NOT_EXECUTED"}


@router.get("/a2a/messages/{workflow_id}")
def a2a_messages(workflow_id: int, db: Db) -> Any:
    return [x.payload_json for x in db.scalars(select(A2AMessageRecord).where(A2AMessageRecord.workflow_id == workflow_id)).all()]


@router.post("/reasoning/gemini")
def gemini_reasoning(request: EvidenceReasoningRequest, db: Db, authorization: Annotated[str | None, Header()] = None) -> Any:
    authorize(authorization); return reason_with_gemini(db, request)


@router.post("/gemma/policy/review")
def gemma_review(request: PolicyReviewRequest, db: Db, authorization: Annotated[str | None, Header()] = None) -> Any:
    authorize(authorization); return review_with_gemma(db, request)


@router.post("/gemma/evidence/check")
def gemma_evidence(request: PolicyReviewRequest, db: Db, authorization: Annotated[str | None, Header()] = None) -> Any:
    authorize(authorization); return review_with_gemma(db, request)


@router.get("/forecasts/{workflow_id}/supplemental")
def vertex_forecast(workflow_id: int, db: Db) -> Any:
    run = db.get(NexusRun, workflow_id)
    if not run: raise HTTPException(404, "Workflow not found")
    return supplemental_forecast(db, run)


@router.get("/mcp/tools")
def mcp_tools() -> Any: return [{"name": name, "production_mutation": False} for name in sorted(TOOLS)]


@router.post("/mcp/tools/{tool_name}")
def call_tool(tool_name: str, request: ToolCall, db: Db, authorization: Annotated[str | None, Header()] = None) -> Any:
    authorize(authorization)
    if tool_name not in TOOLS: raise HTTPException(404, "Unknown tool")
    run = db.get(NexusRun, request.workflow_id)
    if not run: raise HTTPException(404, "Workflow not found")
    values: dict[str, Any] = {"get_evidence": [x.payload_json for x in db.scalars(select(NexusEvidence).where(NexusEvidence.run_id == run.id)).all()],
        "get_tournament_results": run.tournament_json, "get_gate_results": [g for c in run.tournament_json.get("candidates", []) for g in c.get("gates", [])],
        "calculate_business_impact": run.impact_json, "create_twin_manifest": run.twin_json,
        "get_scenario_result": run.scenarios_json, "run_scenario": run.scenarios_json,
        "get_latest_metrics": run.forecast_json, "get_telemetry": run.forecast_json,
        "get_service_topology": {"services": ["payment", "redis"]}, "get_slo_configuration": {"p95_ms": 500},
        "get_incident_history": [], "export_evidence_package": {"available": run.state == "DECIDED"}}
    return {"tool": tool_name, "result": values[tool_name], "correlation_id": request.correlation_id,
        "production_action": "NOT_EXECUTED", "executed_at": utcnow().isoformat()}
