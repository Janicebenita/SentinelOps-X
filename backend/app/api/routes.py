from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..agent import workflow
from ..agent.state import AgentState
from ..database import get_db
from ..models import *
from ..schemas import ApprovalInput, CounterfactualInput, IncidentCreate, IncidentRead, ReplayInput
from ..services.audit import transition
from ..services.demo_seed import ensure_seeded
from ..services import finale, nexus
router=APIRouter(prefix="/api")
def serialize(row): return {c.name:getattr(row,c.name) for c in row.__table__.columns}
@router.get("/nexus/operational-twin")
def nexus_twin(load_multiplier:float=1.0,redis_capacity:int=12000):
    try:return nexus.build_operational_twin(load_multiplier,redis_capacity)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.post("/incidents",response_model=IncidentRead)
def create(payload:IncidentCreate,db:Session=Depends(get_db)):
    row=Incident(**payload.model_dump()); db.add(row); db.commit(); db.refresh(row); return row
@router.get("/incidents")
def list_incidents(db:Session=Depends(get_db)): return [serialize(x) for x in db.scalars(select(Incident).order_by(Incident.id.desc()))]
@router.get("/incidents/{iid}")
def get_incident(iid:int,db:Session=Depends(get_db)): return serialize(workflow.require(db,iid))
@router.post("/incidents/{iid}/start")
def start(iid:int,db:Session=Depends(get_db)): return serialize(transition(db,workflow.require(db,iid),AgentState.ALERT_RECEIVED,actor="user"))
@router.post("/incidents/{iid}/collect-evidence")
def collect(iid:int,db:Session=Depends(get_db)): return [serialize(x) for x in workflow.collect_evidence(db,workflow.require(db,iid))]
@router.post("/incidents/{iid}/generate-hypotheses")
def gen_h(iid:int,db:Session=Depends(get_db)): return [serialize(x) for x in workflow.hypotheses(db,workflow.require(db,iid))]
@router.post("/incidents/{iid}/reproduce")
def repro(iid:int,db:Session=Depends(get_db)): return serialize(workflow.reproduce(db,workflow.require(db,iid)))
@router.post("/incidents/{iid}/generate-patch")
def patch(iid:int,db:Session=Depends(get_db)): return serialize(workflow.generate_patch(db,workflow.require(db,iid)))
@router.post("/incidents/{iid}/verify")
def verify(iid:int,db:Session=Depends(get_db)): return [serialize(x) for x in workflow.verify(db,workflow.require(db,iid))]
@router.post("/incidents/{iid}/approve")
def approve(iid:int,payload:ApprovalInput,db:Session=Depends(get_db)): workflow.approve(db,workflow.require(db,iid),payload.approved_by,True); return {"approved":True}
@router.post("/incidents/{iid}/reject")
def reject(iid:int,payload:ApprovalInput,db:Session=Depends(get_db)): workflow.approve(db,workflow.require(db,iid),payload.approved_by,False); return {"approved":False}
@router.post("/incidents/{iid}/create-pr")
def pr(iid:int,db:Session=Depends(get_db)):
    try:return serialize(workflow.create_pr(db,workflow.require(db,iid)))
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc
def listing(model,iid,db): return [serialize(x) for x in db.scalars(select(model).where(model.incident_id==iid))]
@router.get("/incidents/{iid}/evidence")
def evidence(iid:int,db:Session=Depends(get_db)): return listing(EvidenceItem,iid,db)
@router.get("/incidents/{iid}/hypotheses")
def hyp(iid:int,db:Session=Depends(get_db)): return listing(Hypothesis,iid,db)
@router.get("/incidents/{iid}/patches")
def patches(iid:int,db:Session=Depends(get_db)): return listing(PatchCandidate,iid,db)
@router.get("/incidents/{iid}/pull-requests")
def pull_requests(iid:int,db:Session=Depends(get_db)): return listing(PullRequestRecord,iid,db)
@router.get("/incidents/{iid}/verification")
def verification(iid:int,db:Session=Depends(get_db)):
    ids=select(PatchCandidate.id).where(PatchCandidate.incident_id==iid); return [serialize(x) for x in db.scalars(select(VerificationRun).where(VerificationRun.patch_candidate_id.in_(ids)))]
@router.get("/incidents/{iid}/timeline")
@router.get("/incidents/{iid}/audit-log")
def timeline(iid:int,db:Session=Depends(get_db)): return listing(AuditEvent,iid,db)
@router.post("/demo/seed")
def seed(db:Session=Depends(get_db)):
    seeded, ids = ensure_seeded(db)
    return {"seeded": seeded, "ids": ids, "reason": None if seeded else "already seeded"}
@router.post("/demo/trigger-incident")
def trigger(db:Session=Depends(get_db)):
    row=db.scalar(select(Incident).order_by(Incident.id));
    if row is None: raise HTTPException(404,"Seed an incident first")
    if row.current_state=="NEW": transition(db,row,AgentState.ALERT_RECEIVED,actor="demo-alert")
    return serialize(row)
@router.post("/demo/generate-traffic")
def traffic(): return {"generated":True,"message":"Use scripts/generate_traffic.py against the demo app"}
@router.post("/demo/reset")
def reset(db:Session=Depends(get_db)):
    for model in [IncidentPackage,AuditChainEvent,RedTeamReview,EvidenceLink,BlastRadiusEstimate,ScenarioResult,CounterfactualScenario,CandidateVerification,RepairCandidate,ReplayRun,TwinManifest,PullRequestRecord,AuditEvent,ApprovalRequest,VerificationRun,PatchCandidate,ReproductionAttempt,Hypothesis,EvidenceItem,Incident]: db.execute(__import__('sqlalchemy').delete(model))
    db.commit(); return {"reset":True}

@router.post("/incidents/{iid}/digital-twin")
def digital_twin(iid:int,db:Session=Depends(get_db)): return serialize(finale.create_twin(db,workflow.require(db,iid)))
@router.get("/incidents/{iid}/digital-twin")
def get_digital_twin(iid:int,db:Session=Depends(get_db)):
    row=db.scalar(select(TwinManifest).where(TwinManifest.incident_id==iid));
    if row is None: raise HTTPException(404,"Digital twin not created")
    return serialize(row)
@router.post("/incidents/{iid}/replay")
def replay(iid:int,payload:ReplayInput=ReplayInput(),db:Session=Depends(get_db)): return [serialize(x) for x in finale.replay_incident(db,workflow.require(db,iid),payload.candidate_id,payload.attempts)]
@router.get("/incidents/{iid}/replays")
def replays(iid:int,db:Session=Depends(get_db)): return listing(ReplayRun,iid,db)
@router.post("/incidents/{iid}/repair-tournament")
def tournament(iid:int,db:Session=Depends(get_db)): return finale.run_tournament(db,workflow.require(db,iid))
@router.get("/incidents/{iid}/repair-tournament")
def tournament_results(iid:int,db:Session=Depends(get_db)):
    candidates=listing(RepairCandidate,iid,db);checks=listing(CandidateVerification,iid,db);blasts=listing(BlastRadiusEstimate,iid,db);reviews=listing(RedTeamReview,iid,db)
    return {"candidates":candidates,"checks":checks,"blast_radius":blasts,"red_team":reviews,"recommended_candidate":next((x for x in sorted(candidates,key=lambda x:x["score"],reverse=True) if x["eligible"]),None),"weights":finale.WEIGHTS}
@router.post("/incidents/{iid}/counterfactuals")
def counterfactuals(iid:int,db:Session=Depends(get_db)): return [serialize(x) for x in finale.run_counterfactuals(db,workflow.require(db,iid))]
@router.post("/incidents/{iid}/counterfactuals/custom")
def custom_counterfactual(iid:int,payload:CounterfactualInput,db:Session=Depends(get_db)): return [serialize(x) for x in finale.run_custom_counterfactual(db,workflow.require(db,iid),payload.model_dump())]
@router.get("/incidents/{iid}/counterfactuals")
def counterfactual_results(iid:int,db:Session=Depends(get_db)): return listing(ScenarioResult,iid,db)
@router.get("/incidents/{iid}/evidence-links")
def evidence_links(iid:int,db:Session=Depends(get_db)): return [serialize(x) for x in finale.create_evidence_links(db,workflow.require(db,iid))]
@router.get("/incidents/{iid}/scorecard")
def reliability_scorecard(iid:int,db:Session=Depends(get_db)): return finale.scorecard(db,workflow.require(db,iid))
@router.post("/incidents/{iid}/audit-package")
def audit_package(iid:int,db:Session=Depends(get_db)): return serialize(finale.export_package(db,workflow.require(db,iid)))
@router.post("/incidents/{iid}/audit-package/verify")
def verify_audit_package(iid:int,db:Session=Depends(get_db)):
    row=db.scalar(select(IncidentPackage).where(IncidentPackage.incident_id==iid).order_by(IncidentPackage.id.desc()));
    if row is None: raise HTTPException(404,"Audit package not created")
    valid=finale.verify_package(row);row.verified=valid;db.commit();return {"verified":valid,"package_hash":row.package_hash,"final_audit_hash":row.final_audit_hash}
@router.get("/incidents/{iid}/audit-package")
def get_audit_package(iid:int,db:Session=Depends(get_db)):
    row=db.scalar(select(IncidentPackage).where(IncidentPackage.incident_id==iid).order_by(IncidentPackage.id.desc()));
    if row is None: raise HTTPException(404,"Audit package not created")
    return serialize(row)
@router.get("/incidents/{iid}/audit-package/report")
def audit_report(iid:int,db:Session=Depends(get_db)):
    row=db.scalar(select(IncidentPackage).where(IncidentPackage.incident_id==iid).order_by(IncidentPackage.id.desc()));
    if row is None: raise HTTPException(404,"Audit package not created")
    return Response(finale.executive_report(row),media_type="text/markdown",headers={"Content-Disposition":f'attachment; filename="sentinelops-incident-{iid}.md"'})
@router.get("/incidents/{iid}/audit-package/bundle")
def audit_bundle(iid:int,db:Session=Depends(get_db)):
    row=db.scalar(select(IncidentPackage).where(IncidentPackage.incident_id==iid).order_by(IncidentPackage.id.desc()));
    if row is None: raise HTTPException(404,"Audit package not created")
    return Response(finale.evidence_zip(row),media_type="application/zip",headers={"Content-Disposition":f'attachment; filename="sentinelops-incident-{iid}-evidence.zip"'})
