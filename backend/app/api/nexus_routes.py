from __future__ import annotations

import json
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import NexusAuditEvent, NexusEvidence, NexusRun
from ..schemas.nexus_contracts import EvidenceUpload, HumanDecisionInput, RunCreate, TwinControls
from ..services import nexus_workflow as workflow

router = APIRouter(prefix="/api/v1", tags=["SentinelOps Nexus"])
Db = Annotated[Session, Depends(get_db)]


def _run(db: Session, run_id: int) -> NexusRun:
    try:
        return workflow.require_run(db, run_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _action(call: Callable[[], Any]) -> Any:
    try:
        return call()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "service": "sentinelops-nexus-api", "production_action": "NOT EXECUTED"}


@router.get("/readiness")
def readiness(db: Db) -> dict[str, object]:
    db.execute(text("SELECT 1"))
    return {"ready": True, "database": True, "provider": "deterministic", "production_action": "NOT EXECUTED"}


@router.post("/demo/reset")
def reset_demo(db: Db) -> dict[str, object]:
    workflow.reset(db)
    return {"reset": True, "production_action": "NOT EXECUTED"}


@router.post("/demo/seed")
def seed_demo(db: Db) -> dict[str, Any]:
    return workflow.serialize(workflow.create_run(db, RunCreate(name="Payment Service capacity forecast")))


@router.get("/demo/status")
def demo_status(db: Db) -> dict[str, Any]:
    latest = db.scalar(select(NexusRun).order_by(NexusRun.id.desc()))
    return {"seeded": latest is not None, "latest": workflow.serialize(latest) if latest else None}


@router.get("/telemetry")
def telemetry(run_id: int, db: Db) -> list[dict[str, Any]]:
    controls = TwinControls.model_validate(_run(db, run_id).inputs_json)
    return [point.model_dump(mode="json") for point in workflow.telemetry(controls)]


@router.post("/workflows")
def create_workflow(payload: RunCreate, db: Db) -> dict[str, Any]:
    return workflow.serialize(workflow.create_run(db, payload))


@router.get("/workflows")
def list_workflows(db: Db) -> list[dict[str, Any]]:
    return [workflow.serialize(row) for row in db.scalars(select(NexusRun).order_by(NexusRun.id.desc())).all()]


@router.get("/workflows/{run_id}")
def get_workflow(run_id: int, db: Db) -> dict[str, Any]:
    return workflow.serialize(_run(db, run_id))


@router.post("/workflows/{run_id}/observe")
def observe(run_id: int, db: Db) -> Any:
    return _action(lambda: workflow.observe(db, _run(db, run_id)))


@router.post("/workflows/{run_id}/predict")
def predict(run_id: int, db: Db) -> Any:
    return _action(lambda: workflow.predict(db, _run(db, run_id)))


@router.post("/workflows/{run_id}/build-twin")
def build_twin(run_id: int, db: Db) -> Any:
    return _action(lambda: workflow.build_twin(db, _run(db, run_id)))


@router.post("/workflows/{run_id}/simulate")
def simulate(run_id: int, db: Db) -> Any:
    return _action(lambda: workflow.simulate(db, _run(db, run_id)))


@router.post("/workflows/{run_id}/tournament")
def tournament(run_id: int, db: Db) -> Any:
    return _action(lambda: workflow.tournament(db, _run(db, run_id)))


@router.post("/workflows/{run_id}/verify")
def verify(run_id: int, db: Db) -> Any:
    return _action(lambda: workflow.verify(db, _run(db, run_id)))


@router.post("/workflows/{run_id}/business-impact")
def business_impact(run_id: int, db: Db) -> Any:
    return _action(lambda: workflow.impact(db, _run(db, run_id)))


@router.post("/workflows/{run_id}/recommend")
def recommend(run_id: int, db: Db) -> Any:
    return _action(lambda: workflow.recommend(db, _run(db, run_id)))


@router.post("/workflows/{run_id}/run-all")
def run_all(run_id: int, db: Db) -> dict[str, Any]:
    return _action(lambda: workflow.serialize(workflow.run_all(db, _run(db, run_id))))


def _decide(run_id: int, payload: HumanDecisionInput, expected: str, db: Session) -> dict[str, Any]:
    if payload.decision != expected:
        raise HTTPException(status_code=422, detail="Decision does not match endpoint")
    return _action(lambda: workflow.decide(db, _run(db, run_id), payload))


@router.post("/workflows/{run_id}/approve")
def approve(run_id: int, payload: HumanDecisionInput, db: Db) -> dict[str, Any]:
    return _decide(run_id, payload, "approve", db)


@router.post("/workflows/{run_id}/reject")
def reject(run_id: int, payload: HumanDecisionInput, db: Db) -> dict[str, Any]:
    return _decide(run_id, payload, "reject", db)


@router.post("/workflows/{run_id}/request-evidence")
def request_evidence(run_id: int, payload: HumanDecisionInput, db: Db) -> dict[str, Any]:
    return _decide(run_id, payload, "request_more_evidence", db)


@router.get("/workflows/{run_id}/timeline")
def timeline(run_id: int, db: Db) -> list[dict[str, Any]]:
    _run(db, run_id)
    rows = db.scalars(select(NexusAuditEvent).where(NexusAuditEvent.run_id == run_id).order_by(NexusAuditEvent.sequence)).all()
    return [workflow.serialize(row) for row in rows]


@router.get("/workflows/{run_id}/events")
def events(run_id: int, db: Db) -> StreamingResponse:
    rows = timeline(run_id, db)
    stream = (f"event: audit\ndata: {json.dumps(row, default=str)}\n\n" for row in rows)
    return StreamingResponse(stream, media_type="text/event-stream")


@router.get("/workflows/{run_id}/evidence")
def evidence(run_id: int, db: Db) -> list[dict[str, Any]]:
    _run(db, run_id)
    rows = db.scalars(select(NexusEvidence).where(NexusEvidence.run_id == run_id).order_by(NexusEvidence.id)).all()
    return [workflow.serialize(row) for row in rows]


@router.post("/workflows/{run_id}/evidence/upload")
def upload_evidence(run_id: int, payload: EvidenceUpload, db: Db) -> dict[str, Any]:
    return workflow.serialize(_action(lambda: workflow.upload_evidence(db, _run(db, run_id), payload)))


@router.get("/workflows/{run_id}/agents")
def agents(run_id: int, db: Db) -> Any:
    return workflow.agent_envelopes(db, _run(db, run_id))


@router.get("/workflows/{run_id}/export")
def export(run_id: int, db: Db) -> Response:
    content = _action(lambda: workflow.export_zip(db, _run(db, run_id)))
    return Response(content, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="sentinelops-nexus-{run_id}.zip"'})


@router.get("/audit/verify")
def audit_verify(run_id: int, db: Db) -> dict[str, Any]:
    _run(db, run_id)
    return workflow.verify_audit(db, run_id)
