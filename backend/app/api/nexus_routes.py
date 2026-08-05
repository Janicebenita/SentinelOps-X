from __future__ import annotations

import json
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response, StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth.roles import AuthError, verify_access_code, verify_token
from ..models import HumanDecision, NexusAuditEvent, NexusEvidence, NexusRun, VerificationRecord
from ..schemas.nexus_contracts import EvidenceUpload, HumanDecisionInput, RunCreate, TwinControls
from ..schemas.upgrade_contracts import AgentActionRequest, AuthorizedDecision, RoleVerifyRequest
from ..services import nexus_workflow as workflow
from ..services import workforce

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


def _auth_error(exc: AuthError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code,content={"code":exc.code,"message":exc.message,"production_action":"NOT_EXECUTED"})


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


@router.post("/demo/bootstrap")
def bootstrap_demo(db: Db) -> dict[str, Any]:
    """Return a ready workflow in one request, minimizing free-tier wake-up round trips."""
    run = db.scalar(select(NexusRun).order_by(NexusRun.id.desc()))
    if run is None:
        run = workflow.create_run(db, RunCreate(name="Payment Service capacity forecast"))
    return workflow.serialize(workflow.run_all(db, run))


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


def _decide(run_id: int, payload: AuthorizedDecision, expected: str, db: Session) -> dict[str, Any] | JSONResponse:
    if payload.decision != expected:
        raise HTTPException(status_code=422, detail="Decision does not match endpoint")
    try: token,verification=verify_token(db,payload.verification_token)
    except AuthError as exc: return _auth_error(exc)
    run=_run(db,run_id)
    if token["sub"] != payload.actor_name: return JSONResponse(status_code=403,content={"code":"ACTOR_TOKEN_MISMATCH","message":"Verified actor does not match decision actor.","production_action":"NOT_EXECUTED"})
    if expected=="approve" and token["role"]!="SENIOR_DEVELOPER":
        workflow.append_event(db,run,"approval.blocked",payload.actor_name,{"role":token["role"],"reason":"APPROVER_NOT_QUALIFIED"})
        return JSONResponse(status_code=403,content={"code":"APPROVER_NOT_QUALIFIED","message":"Approval requires the Senior Developer role.","production_action":"NOT_EXECUTED"})
    if run.state != "AWAITING_HUMAN": raise HTTPException(status_code=409,detail="Workflow is not awaiting human review")
    tournament=run.tournament_json; candidate=next((x for x in tournament.get("candidates",[]) if x.get("candidate_id")==tournament.get("recommended_candidate_id")),None)
    if not candidate or not candidate.get("eligible") or not all(g.get("passed") for g in candidate.get("gates",[]) if g.get("mandatory",True)): raise HTTPException(status_code=409,detail="Recommended candidate is not eligible or mandatory gates failed")
    if run.production_action_executed: raise HTTPException(status_code=409,detail="Production execution safety boundary is not ready")
    technical=workforce.technical_verification(db,run)
    if technical.result!="VERIFIED": raise HTTPException(status_code=409,detail="Verification Agent rejected approval readiness")
    qualification_checks={"access_code_valid":True,"role_mapped":token["role"] in {"INTERN","SENIOR_DEVELOPER"},"approval_permission":expected!="approve" or token["role"]=="SENIOR_DEVELOPER","workflow_state":run.state=="AWAITING_HUMAN","candidate_eligible":bool(candidate and candidate.get("eligible")),"mandatory_rationale":len(payload.rationale.strip())>=3,"audit_ready":workflow.verify_audit(db,run.id)["valid"],"production_execution_disabled":not run.production_action_executed}
    qualification_failed=[name for name,passed in qualification_checks.items() if not passed]
    qualification=VerificationRecord(workflow_id=run.id,subject_type="approver",subject_id=payload.actor_name,result="VERIFIED" if not qualification_failed else "REJECTED",checks=qualification_checks,failed_checks=qualification_failed,evidence_ids=technical.evidence_ids,reason="Approver and decision qualification verified." if not qualification_failed else "Decision qualification failed: "+", ".join(qualification_failed),audit_event_id=technical.audit_event_id); db.add(qualification); db.commit()
    if qualification_failed: raise HTTPException(status_code=409,detail=qualification.reason)
    if expected=="approve": workflow.append_event(db,run,"approval.enabled",payload.actor_name,{"role":token["role"],"action":"approve","object_type":"workflow","object_id":run.id,"result":"enabled","evidence_references":technical.evidence_ids})
    action={"approve":"approval.submitted","reject":"rejection.submitted","request_more_evidence":"more_evidence.requested"}[expected]
    workflow.append_event(db,run,action,payload.actor_name,{"role":token["role"],"action":expected,"object_type":"workflow","object_id":run.id,"result":"submitted","evidence_references":technical.evidence_ids,"production_action":"NOT_EXECUTED"})
    decision_input=HumanDecisionInput(actor=payload.actor_name,decision=payload.decision,rationale=payload.rationale)
    result=_action(lambda: workflow.decide(db,run,decision_input))
    decision_event=db.scalar(select(NexusAuditEvent).where(NexusAuditEvent.run_id==run.id).order_by(NexusAuditEvent.sequence.desc()))
    record=HumanDecision(workflow_id=run.id,actor_name=payload.actor_name,actor_role=token["role"],decision=payload.decision,rationale=payload.rationale,role_verification_id=verification.id,audit_event_id=decision_event.id if decision_event else None,production_action="NOT_EXECUTED"); db.add(record); db.commit(); db.refresh(record)
    return {**result,"actor_role":token["role"],"decision_id":record.id}


@router.post("/workflows/{run_id}/approve")
def approve(run_id: int, payload: AuthorizedDecision, db: Db) -> Any:
    return _decide(run_id, payload, "approve", db)


@router.post("/workflows/{run_id}/reject")
def reject(run_id: int, payload: AuthorizedDecision, db: Db) -> Any:
    return _decide(run_id, payload, "reject", db)


@router.post("/workflows/{run_id}/request-evidence")
def request_evidence(run_id: int, payload: AuthorizedDecision, db: Db) -> Any:
    return _decide(run_id, payload, "request_more_evidence", db)


@router.get("/workflows/{run_id}/timeline")
def timeline(run_id: int, db: Db, limit: int = 200, offset: int = 0) -> list[dict[str, Any]]:
    _run(db, run_id)
    limit=max(1,min(limit,500)); offset=max(0,offset)
    rows = db.scalars(select(NexusAuditEvent).where(NexusAuditEvent.run_id == run_id).order_by(NexusAuditEvent.sequence).offset(offset).limit(limit)).all()
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
    run=_run(db,run_id); return [workforce.workspace(db,name,run) for name in workforce.AGENTS]


@router.get("/agents")
def agent_catalogue() -> Any: return workforce.catalogue()


@router.get("/agents/{agent_name}")
def agent_definition(agent_name: str) -> Any:
    try: return workforce.workspace(None,agent_name)  # type: ignore[arg-type]
    except LookupError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc


@router.get("/agents/{agent_name}/status")
def agent_status(agent_name: str) -> Any: return agent_definition(agent_name)


@router.get("/workflows/{run_id}/agents/{agent_name}")
def workflow_agent(run_id: int,agent_name: str,db: Db) -> Any:
    try:
        run=_run(db,run_id); result=workforce.workspace(db,agent_name,run)
        workflow.append_event(db,run,"agent.opened","human-operator",{"agent_name":agent_name,"object_type":"agent","object_id":agent_name,"result":"opened","evidence_references":result.evidence_references})
        return result
    except LookupError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc


@router.post("/workflows/{run_id}/agents/{agent_name}/run")
def run_agent(run_id: int,agent_name: str,payload: AgentActionRequest,db: Db) -> Any:
    return _action(lambda: workforce.execute(db,_run(db,run_id),agent_name,payload.actor_name))


@router.post("/workflows/{run_id}/agents/{agent_name}/rerun")
def rerun_agent(run_id: int,agent_name: str,payload: AgentActionRequest,db: Db) -> Any:
    return _action(lambda: workforce.execute(db,_run(db,run_id),agent_name,payload.actor_name,True))


@router.get("/workflows/{run_id}/agents/{agent_name}/events")
def agent_events(run_id: int,agent_name: str,db: Db) -> Any:
    _run(db,run_id); return workforce.events(db,run_id,agent_name)


@router.get("/workflows/{run_id}/verification")
def verification_results(run_id: int,db: Db) -> Any:
    _run(db,run_id); return [workflow.serialize(x) for x in db.scalars(select(VerificationRecord).where(VerificationRecord.workflow_id==run_id).order_by(VerificationRecord.id.desc()))]


@router.post("/workflows/{run_id}/verification/run")
def run_verification(run_id: int,db: Db) -> Any: return workforce.technical_verification(db,_run(db,run_id))


@router.post("/auth/verify-role")
def verify_role(payload: RoleVerifyRequest,db: Db) -> Any:
    latest=db.scalar(select(NexusRun).order_by(NexusRun.id.desc()))
    if latest: workflow.append_event(db,latest,"role.verification_attempted",payload.actor_name,{"code_fingerprint":"redacted"})
    try: row,token,permissions=verify_access_code(db,payload.actor_name,payload.access_code)
    except AuthError as exc:
        if latest:
            event=workflow.append_event(db,latest,"role.verification_failed",payload.actor_name,{"reason":exc.code})
            record=VerificationRecord(workflow_id=latest.id,subject_type="approver",subject_id=payload.actor_name,result="REJECTED",checks={"access_code_valid":False,"role_mapped":False,"approval_permission":False},failed_checks=["access_code_valid","role_mapped","approval_permission"],evidence_ids=[],reason="Access code verification failed.",audit_event_id=event.id); db.add(record); db.commit()
        return _auth_error(exc)
    if latest:
        event=workflow.append_event(db,latest,"role.verification_succeeded",payload.actor_name,{"role":row.role,"token_id":row.token_id,"expires_at":row.expires_at.isoformat()}); row.audit_event_id=event.id; db.commit()
        approval_allowed=row.role=="SENIOR_DEVELOPER"; candidate=latest.tournament_json.get("recommended_candidate_id")
        checks={"access_code_valid":True,"role_mapped":True,"approval_permission":approval_allowed,"workflow_state":latest.state=="AWAITING_HUMAN","candidate_eligible":bool(candidate),"mandatory_rationale":False,"audit_ready":workflow.verify_audit(db,latest.id)["valid"]}
        failed=[name for name,passed in checks.items() if not passed]; denied=not approval_allowed or any(name not in {"mandatory_rationale"} for name in failed); result="REJECTED" if denied else "MORE_INFORMATION_REQUIRED"; qualification=VerificationRecord(workflow_id=latest.id,subject_type="approver",subject_id=payload.actor_name,result=result,checks=checks,failed_checks=failed,evidence_ids=[],reason="Role verified; mandatory rationale is required to complete qualification." if result=="MORE_INFORMATION_REQUIRED" else "Role verified; approval qualification failed: "+", ".join(failed),audit_event_id=event.id); db.add(qualification); db.commit()
    return {"verified":True,"role":row.role,"permissions":permissions,"expires_at":row.expires_at,"verification_token":token}


@router.get("/workflows/{run_id}/export")
def export(run_id: int, db: Db) -> Response:
    content = _action(lambda: workflow.export_zip(db, _run(db, run_id)))
    return Response(content, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="sentinelops-nexus-{run_id}.zip"'})


@router.get("/audit/verify")
def audit_verify(run_id: int, db: Db) -> dict[str, Any]:
    _run(db, run_id)
    return workflow.verify_audit(db, run_id)
