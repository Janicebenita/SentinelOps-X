from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AgentExecution, NexusAuditEvent, NexusEvidence, NexusRun, VerificationRecord
from ..schemas.upgrade_contracts import AgentWorkspace, VerificationResult
from . import nexus_workflow as workflow

AGENTS: dict[str, dict[str, Any]] = {
    "nexus-orchestrator":{"display":"Nexus Orchestrator","purpose":"Coordinates the bounded workflow without executing production changes.","responsibilities":["validate state","coordinate agents","enforce non-execution"]},
    "observer-agent":{"display":"Observer Agent","purpose":"Normalises the deterministic operational window.","responsibilities":["collect telemetry","persist observations","reference evidence"]},
    "evidence-agent":{"display":"Evidence Agent","purpose":"Validates and catalogues operational evidence.","responsibilities":["inspect evidence","verify hashes","report gaps"]},
    "process-discovery-agent":{"display":"Process Discovery Agent","purpose":"Reconstructs the service topology and critical path.","responsibilities":["map services","identify dependencies","locate constraints"]},
    "prediction-agent":{"display":"Prediction Agent","purpose":"Forecasts the next safe-capacity crossing.","responsibilities":["calculate forecast","state assumptions","report confidence"]},
    "digital-twin-agent":{"display":"Digital Twin Agent","purpose":"Builds the bounded deterministic Twin manifest.","responsibilities":["bind evidence","hash configuration","enforce resource limits"]},
    "simulation-agent":{"display":"Simulation Agent","purpose":"Runs twelve deterministic counterfactual scenarios.","responsibilities":["replay scenarios","calculate outcomes","persist result hashes"]},
    "optimization-agent":{"display":"Optimization Agent","purpose":"Ranks eligible interventions after mandatory gates.","responsibilities":["score FAST SAFE OPTIMAL","enforce eligibility","recommend candidate"]},
    "verification-agent":{"display":"Verification Agent","purpose":"Verifies technical evidence and approver qualification; it never approves.","responsibilities":["verify gates","verify audit readiness","verify approver qualification"]},
    "business-impact-agent":{"display":"Business Impact Agent","purpose":"Estimates customer and commercial exposure from visible assumptions.","responsibilities":["estimate exposure","show formula","state limitations"]},
    "executive-agent":{"display":"Executive Agent","purpose":"Creates the evidence-backed decision brief.","responsibilities":["summarise finding","explain recommendation","show uncertainty"]},
}


def catalogue() -> list[dict[str, Any]]:
    return [{"agent_name":name,"display_name":value["display"],"purpose":value["purpose"],"responsibilities":value["responsibilities"],"supported_actions":["view_details","view_inputs","view_outputs","view_evidence","run","rerun","view_audit_events"]} for name,value in AGENTS.items()]


def _artifacts(run: NexusRun, name: str) -> tuple[Any, Any, list[str], list[str]]:
    controls=run.inputs_json; evidence=["ev-telemetry","ev-config","ev-topology","ev-slo"]
    outputs={"nexus-orchestrator":{"state":run.state},"observer-agent":controls,"evidence-agent":{"evidence_count":4},"process-discovery-agent":{"critical_path":["checkout-api","payment-service","redis-primary"]},"prediction-agent":run.forecast_json,"digital-twin-agent":run.twin_json,"simulation-agent":run.scenarios_json,"optimization-agent":run.tournament_json,"verification-agent":{"state":run.state},"business-impact-agent":run.impact_json,"executive-agent":run.recommendation_json}
    assumptions=list(run.forecast_json.get("assumptions",[])) if run.forecast_json else []
    return controls,outputs.get(name,{}),evidence,assumptions


def workspace(db: Session, name: str, run: NexusRun | None = None) -> AgentWorkspace:
    if name not in AGENTS: raise LookupError("Agent not found")
    execution=None
    if run is not None: execution=db.scalar(select(AgentExecution).where(AgentExecution.workflow_id==run.id,AgentExecution.agent_name==name).order_by(AgentExecution.id.desc()))
    inp,out,evidence,assumptions=_artifacts(run,name) if run else (None,None,[],[])
    meta=AGENTS[name]
    return AgentWorkspace(agent_name=name,display_name=meta["display"],purpose=meta["purpose"],responsibilities=meta["responsibilities"],current_status=execution.status if execution else (run.state if run else "AVAILABLE"),workflow_id=run.id if run else None,last_execution_time=execution.completed_at if execution else None,execution_duration_ms=execution.execution_duration_ms if execution else None,input_artifact=inp,output_artifact=out,evidence_references=evidence,assumptions=assumptions,errors=execution.error if execution else None,retry_count=execution.retry_count if execution else 0,result_hash=execution.result_hash if execution else None,supported_actions=["view_details","view_inputs","view_outputs","view_evidence","run","rerun","view_audit_events"],reasoning_summary=f"{meta['display']} exposes structured outputs and evidence only; hidden chain-of-thought is never displayed.")


def _technical_checks(db: Session, run: NexusRun) -> dict[str, bool]:
    candidates=run.tournament_json.get("candidates",[]); recommended=run.tournament_json.get("recommended_candidate_id"); winner=next((x for x in candidates if x.get("candidate_id")==recommended),None)
    gates=winner.get("gates",[]) if winner else []
    scenarios=run.scenarios_json
    return {"baseline_replay":any(x.get("scenario_id")=="baseline-growth" for x in scenarios),"bottleneck_reproduction":any(x.get("status")=="fail" for x in scenarios),"deterministic_replay":bool(scenarios) and all(len(x.get("result_hash",""))==64 for x in scenarios),"failover_safety":any(x.get("gate")=="failover_test" and x.get("passed") for x in gates),"performance_gate":any(x.get("gate")=="performance_gate" and x.get("passed") for x in gates),"configuration_policy":any(x.get("gate")=="configuration_policy_gate" and x.get("passed") for x in gates),"evidence_completeness":len(run.forecast_json.get("evidence_ids",[]))>=3,"audit_completeness":workflow.verify_audit(db,run.id)["valid"],"recommendation_eligibility":bool(winner and winner.get("eligible")),"production_execution_disabled":not run.production_action_executed}


def technical_verification(db: Session, run: NexusRun) -> VerificationResult:
    checks=_technical_checks(db,run); failed=[name for name,passed in checks.items() if not passed]; result: Literal["VERIFIED","REJECTED","MORE_INFORMATION_REQUIRED"]="VERIFIED" if not failed else "REJECTED"; reason="All technical and safety checks passed." if not failed else "Failed checks: "+", ".join(failed)
    row=VerificationRecord(workflow_id=run.id,subject_type="workflow",subject_id=str(run.id),result=result,checks=checks,failed_checks=failed,evidence_ids=["ev-telemetry","ev-config","ev-topology","ev-slo"],reason=reason); db.add(row); db.commit(); db.refresh(row)
    event=workflow.append_event(db,run,"verification.completed","verification-agent",{"result":result,"failed_checks":failed,"production_action":"NOT_EXECUTED"}); row.audit_event_id=event.id; db.commit()
    return VerificationResult(verification_id=row.id,workflow_id=run.id,subject_type=row.subject_type,subject_id=row.subject_id,result=result,checks=checks,failed_checks=failed,evidence_ids=row.evidence_ids,reason=reason,verified_at=row.created_at,verified_by=row.verified_by,audit_event_id=event.id)


def _perform(db: Session, run: NexusRun, name: str) -> Any:
    if name=="nexus-orchestrator": return {"workflow_id":run.id,"state":run.state,"production_action":"NOT_EXECUTED"}
    if name=="observer-agent" and run.state=="CREATED": return workflow.observe(db,run)
    if name=="evidence-agent": return [workflow.serialize(x) for x in db.scalars(select(NexusEvidence).where(NexusEvidence.run_id==run.id))]
    if name=="process-discovery-agent": return workflow.topology(db,run).model_dump(mode="json")
    stages: dict[str, tuple[str, Callable[..., Any]]] = {"prediction-agent":("OBSERVED",workflow.predict),"digital-twin-agent":("PREDICTED",workflow.build_twin),"simulation-agent":("TWIN_READY",workflow.simulate),"optimization-agent":("SIMULATED",workflow.tournament),"business-impact-agent":("VERIFIED",workflow.impact),"executive-agent":("IMPACT_READY",workflow.recommend)}
    if name=="verification-agent":
        if run.state=="TOURNAMENT_READY": workflow.verify(db,run)
        return technical_verification(db,run).model_dump(mode="json")
    expected,call=stages.get(name,("",lambda *_:{}))
    if run.state==expected: return call(db,run)
    return workspace(db,name,run).output_artifact


def execute(db: Session, run: NexusRun, name: str, actor: str, rerun: bool=False) -> AgentWorkspace:
    if name not in AGENTS: raise LookupError("Agent not found")
    previous=db.scalar(select(AgentExecution).where(AgentExecution.workflow_id==run.id,AgentExecution.agent_name==name).order_by(AgentExecution.id.desc())); retry=(previous.retry_count+1 if rerun and previous else 0)
    row=AgentExecution(workflow_id=run.id,agent_name=name,status="RUNNING",started_at=datetime.now(timezone.utc),input_reference=f"workflow:{run.id}:inputs",retry_count=retry); db.add(row); db.commit(); db.refresh(row)
    workflow.append_event(db,run,"agent.rerun_requested" if rerun else "agent.run_requested",actor,{"agent_name":name,"execution_id":row.id})
    started=time.perf_counter()
    try:
        output=_perform(db,run,name); output_hash=workflow.digest(output); row.status="COMPLETED"; row.result_hash=output_hash; row.output_reference=f"sha256:{output_hash}"; row.evidence_ids=["ev-telemetry","ev-config","ev-topology","ev-slo"]
        event_type="agent.run_completed"
    except Exception as exc:
        row.status="FAILED"; row.error=str(exc)[:1000]; event_type="agent.run_failed"
    row.completed_at=datetime.now(timezone.utc); row.execution_duration_ms=round((time.perf_counter()-started)*1000); db.commit()
    workflow.append_event(db,run,event_type,name,{"execution_id":row.id,"status":row.status,"duration_ms":row.execution_duration_ms,"result_hash":row.result_hash,"error":row.error})
    if row.status=="FAILED": raise ValueError(row.error or "Agent execution failed")
    return workspace(db,name,run)


def events(db: Session, run_id: int, name: str) -> list[dict[str, Any]]:
    rows=db.scalars(select(NexusAuditEvent).where(NexusAuditEvent.run_id==run_id,NexusAuditEvent.actor.in_([name,"human-operator"])).order_by(NexusAuditEvent.sequence)).all()
    return [workflow.serialize(x) for x in rows if x.actor==name or x.payload_json.get("agent_name")==name]
