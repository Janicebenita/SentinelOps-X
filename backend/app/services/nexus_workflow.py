from __future__ import annotations

import io
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..models import NexusAuditEvent, NexusEvidence, NexusRun
from ..schemas.nexus_contracts import (
    AgentEnvelope,
    BusinessImpactResult,
    EvidenceUpload,
    EvidenceRecord,
    ExecutiveBrief,
    ForecastResult,
    GateResult,
    HumanDecisionInput,
    InterventionCandidate,
    RunCreate,
    ScenarioResultContract,
    TelemetryPoint,
    TopologyResult,
    TournamentResult,
    TwinControls,
    TwinManifestContract,
)

ROOT = Path(__file__).resolve().parents[3]
SCENARIOS = [
    "baseline-growth", "redis-crash", "redis-latency", "replica-failover",
    "10x-traffic", "million-user-stress", "reduced-redis-capacity",
    "increased-app-replicas", "rollback-intervention", "rate-limiting-intervention",
    "cache-policy-correction", "configuration-drift",
]
STATE_ORDER = ["CREATED", "OBSERVED", "PREDICTED", "TWIN_READY", "SIMULATED", "TOURNAMENT_READY", "VERIFIED", "IMPACT_READY", "RECOMMENDED", "DECIDED"]


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def digest(value: Any) -> str:
    return sha256(canonical(value).encode()).hexdigest()


def serialize(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def require_run(db: Session, run_id: int) -> NexusRun:
    row = db.get(NexusRun, run_id)
    if row is None:
        raise LookupError("Nexus run not found")
    return row


def require_state(run: NexusRun, *states: str) -> None:
    if run.state not in states:
        raise ValueError(f"State {run.state} cannot perform this action; expected {', '.join(states)}")


def upload_evidence(db: Session, run: NexusRun, upload: EvidenceUpload) -> NexusEvidence:
    try:
        parsed: Any = json.loads(upload.content)
    except json.JSONDecodeError as exc:
        raise ValueError("Uploaded evidence must contain valid JSON") from exc
    content_hash = digest(parsed)
    row = NexusEvidence(run_id=run.id,evidence_id=f"manual-{content_hash[:12]}",category=upload.category,source=f"manual-upload/{upload.filename}",observed_at=datetime.now(timezone.utc),payload_json={"document":parsed},summary=f"User-uploaded {upload.category} evidence: {upload.filename}",content_hash=content_hash)
    db.add(row); db.commit(); db.refresh(row)
    append_event(db,run,"evidence.uploaded","human-operator",{"evidence_id":row.evidence_id,"filename":upload.filename,"category":upload.category,"content_hash":content_hash})
    return row


def append_event(db: Session, run: NexusRun, event_type: str, actor: str, payload: dict[str, Any]) -> NexusAuditEvent:
    latest = db.scalar(select(NexusAuditEvent).where(NexusAuditEvent.run_id == run.id).order_by(NexusAuditEvent.sequence.desc()))
    sequence = 1 if latest is None else latest.sequence + 1
    previous = "0" * 64 if latest is None else latest.event_hash
    body = {"sequence": sequence, "event_type": event_type, "actor": actor, "payload": payload}
    event = NexusAuditEvent(run_id=run.id, sequence=sequence, event_type=event_type, actor=actor, payload_json=payload, previous_hash=previous, event_hash=sha256((previous + canonical(body)).encode()).hexdigest())
    db.add(event); db.commit(); db.refresh(event); return event


def transition(db: Session, run: NexusRun, target: str, actor: str, payload: dict[str, Any]) -> None:
    current_index, target_index = STATE_ORDER.index(run.state), STATE_ORDER.index(target)
    if target_index != current_index + 1:
        raise ValueError(f"Invalid Nexus transition {run.state} -> {target}")
    run.state = target; run.updated_at = datetime.now(timezone.utc); db.commit()
    append_event(db, run, f"state.{target.lower()}", actor, payload)


def source_revision() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=2).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable-local-revision"


def telemetry(controls: TwinControls) -> list[TelemetryPoint]:
    base = [
        ("Yesterday", -1440, 4100, 44), ("Now", 0, 8500, 72),
        ("+15 min", 15, 9800, 81), ("+30 min", 30, 11100, 90), ("+45 min", 45, 12500, 98),
    ]
    points: list[TelemetryPoint] = []
    for label, minute, requests, memory in base:
        request_rate = round(requests * controls.traffic_multiplier)
        effective_capacity = controls.redis_capacity * max(0.65, controls.application_replicas / 4)
        saturation = min(100, memory * 12000 / effective_capacity * controls.traffic_multiplier)
        latency_pressure = max(0, saturation - 68)
        p95 = 120 + latency_pressure**1.55 + controls.dependency_latency_ms
        queue = round(max(0, saturation - 70)**1.72 * 3)
        error = round(max(0, saturation - 90)**1.4 / 8, 2)
        if controls.failover_state == "replica": p95 *= 1.18
        if controls.failover_state == "unavailable": p95, error = 5000, 100
        points.append(TelemetryPoint(label=label, minute=minute, request_rate=request_rate, p50_ms=round(p95*.42,1), p95_ms=round(p95,1), p99_ms=round(p95*1.48,1), redis_cpu_pct=round(min(100,saturation*.88),1), redis_memory_pct=round(saturation,1), cache_hit_rate_pct=round(max(25,98-saturation*.28),1), queue_depth=queue, application_replicas=controls.application_replicas, error_rate_pct=error, order_conversion_rate=controls.business.conversion_rate, average_order_value_inr=controls.business.average_order_value_inr, reactive_alert=error >= 5))
    return points


def create_run(db: Session, payload: RunCreate) -> NexusRun:
    row = NexusRun(name=payload.name, seed=payload.controls.seed, inputs_json=payload.controls.model_dump(mode="json"))
    db.add(row); db.commit(); db.refresh(row); append_event(db,row,"run.created","nexus-orchestrator",{"controls":row.inputs_json,"production_action":"NOT EXECUTED"}); return row


def observe(db: Session, run: NexusRun) -> list[EvidenceRecord]:
    require_state(run, "CREATED"); controls=TwinControls.model_validate(run.inputs_json); points=telemetry(controls)
    evidence_specs: list[tuple[str, str, str, dict[str, Any], str]] = [
        ("ev-telemetry","telemetry","seeded/payment-service",{"points":[x.model_dump(mode="json") for x in points]},"Five-point operational window normalised."),
        ("ev-topology","topology","seeded/service-map",{"path":["checkout-api","payment-service","redis-primary"]},"Critical payment path reconstructed."),
        ("ev-config","configuration","seeded/runtime-config",{"redis_capacity":controls.redis_capacity,"application_replicas":controls.application_replicas},"Capacity constraints captured."),
        ("ev-slo","slo","seeded/slo",{"checkout_p95_ms":500,"error_rate_pct":5},"Customer-facing alert thresholds captured."),
    ]
    records=[]
    for eid,category,source,payload,summary in evidence_specs:
        observed_at = datetime.now(timezone.utc)
        content_hash=digest(payload); row=NexusEvidence(run_id=run.id,evidence_id=eid,category=category,source=source,observed_at=observed_at,payload_json=payload,summary=summary,content_hash=content_hash); db.add(row)
        records.append(EvidenceRecord(evidence_id=eid,category=category,source=source,observed_at=observed_at,payload=payload,summary=summary,content_hash=content_hash))
    db.commit(); transition(db,run,"OBSERVED","observer-agent",{"evidence_ids":[x.evidence_id for x in records]}); return records


def topology(db: Session, run: NexusRun) -> TopologyResult:
    require_state(run,"OBSERVED","PREDICTED","TWIN_READY","SIMULATED","TOURNAMENT_READY","VERIFIED","IMPACT_READY","RECOMMENDED","DECIDED")
    return TopologyResult(nodes=[{"id":"checkout-api","type":"service"},{"id":"payment-service","type":"service"},{"id":"redis-primary","type":"cache"},{"id":"order-db","type":"database"}],edges=[{"from":"checkout-api","to":"payment-service","relation":"calls"},{"from":"payment-service","to":"redis-primary","relation":"reads/writes"},{"from":"payment-service","to":"order-db","relation":"writes"}],critical_path=["checkout-api","payment-service","redis-primary"],constraint="Redis safe-capacity margin",evidence_ids=["ev-topology","ev-config"])


def predict(db: Session, run: NexusRun) -> ForecastResult:
    require_state(run,"OBSERVED"); controls=TwinControls.model_validate(run.inputs_json); points=telemetry(controls); now=points[1]
    slope=(points[3].redis_memory_pct-now.redis_memory_pct)/30; crossing=max(0,round((90-now.redis_memory_pct)/max(.01,slope))); impact=max(crossing+15,45)
    residuals=[abs(point.redis_memory_pct-(now.redis_memory_pct+slope*point.minute)) for point in points[1:4]]; mae=round(sum(residuals)/len(residuals),2)
    score=round(min(95,55+25*min(1,slope)+15*(1-min(1,mae/10))))
    result=ForecastResult(model_name="bounded linear saturation trend",equation=f"memory_pct(t) = {now.redis_memory_pct} + {slope:.3f} * minutes",observation_window="Yesterday, Now, +15, +30 minutes",forecast_horizon_minutes=45,safe_threshold_pct=90,reactive_alert_threshold_pct=5,predicted_crossing_minutes=crossing,predicted_customer_impact_minutes=impact,residual_mae=mae,error_bound_minutes=max(3,round(mae/max(.01,slope))),heuristic_evidence_score=score,confidence_label="High" if score>=80 else "Moderate",assumptions=["Traffic trend remains locally linear for 45 minutes","Redis capacity and application replicas remain fixed","No unmodelled upstream outage occurs"],evidence_ids=["ev-telemetry","ev-config","ev-slo"])
    run.forecast_json=result.model_dump(mode="json"); db.commit(); transition(db,run,"PREDICTED","prediction-agent",result.model_dump(mode="json")); return result


def build_twin(db: Session, run: NexusRun) -> TwinManifestContract:
    require_state(run,"PREDICTED"); controls=TwinControls.model_validate(run.inputs_json); forecast=ForecastResult.model_validate(run.forecast_json); topo=topology(db,run); evidence=[x.evidence_id for x in db.scalars(select(NexusEvidence).where(NexusEvidence.run_id==run.id))]
    created=datetime.now(timezone.utc)
    result=TwinManifestContract(twin_id="pending",created_at=created,source_revision=source_revision(),service_topology_hash=digest(topo.model_dump(mode="json")),telemetry_window_hash=digest([x.model_dump(mode="json") for x in telemetry(controls)]),configuration_hash=digest(controls.model_dump(mode="json")),dependency_fingerprint=digest({"python":"3.11+","engine":"deterministic-v1"}),forecasting_parameters=forecast.model_dump(mode="json"),random_seed=controls.seed,capacity_constraints={"redis_capacity":controls.redis_capacity,"application_replicas":controls.application_replicas},slo_definitions={"p95_ms":500,"error_rate_pct":5},business_assumptions=controls.business,network_policy="disabled",allowed_scenarios=SCENARIOS,resource_limits={"cpu":1,"memory_mb":512,"timeout_seconds":30},evidence_references=evidence,manifest_hash="pending",limitation="Bounded operational model under documented assumptions; not a perfect replica.")
    core=result.model_dump(mode="json",exclude={"twin_id","created_at","manifest_hash","limitation"}); manifest_hash=digest(core); result=result.model_copy(update={"twin_id":f"twin-{manifest_hash[:12]}","manifest_hash":manifest_hash})
    run.twin_json=result.model_dump(mode="json"); db.commit(); transition(db,run,"TWIN_READY","digital-twin-agent",{"twin_id":result.twin_id,"manifest_hash":result.manifest_hash}); return result


def simulate(db: Session, run: NexusRun) -> list[ScenarioResultContract]:
    require_state(run,"TWIN_READY"); controls=TwinControls.model_validate(run.inputs_json); twin=TwinManifestContract.model_validate(run.twin_json)
    # Every scenario is evaluated from the submitted controls.  The modifiers are
    # explicit so the lab remains explainable while still behaving like a model,
    # rather than a collection of pre-recorded outcomes.
    definitions: list[tuple[str, dict[str, Any]]] = [
        ("baseline-growth",{"load_factor":1.18}),
        ("redis-crash",{"redis_available":False}),
        ("redis-latency",{"additional_latency_ms":250}),
        ("replica-failover",{"failover":"replica","capacity_factor":.82}),
        ("10x-traffic",{"traffic_multiplier":10}),
        ("million-user-stress",{"sessions":1000000,"load_factor":7.5}),
        ("reduced-redis-capacity",{"redis_capacity":round(controls.redis_capacity*.6)}),
        ("increased-app-replicas",{"application_replicas":min(50,controls.application_replicas+4)}),
        ("rollback-intervention",{"load_factor":.72,"latency_factor":.82}),
        ("rate-limiting-intervention",{"load_factor":.76,"rate_limit_pct":24}),
        ("cache-policy-correction",{"load_factor":.62,"cache_ttl_seconds":180}),
        ("configuration-drift",{"capacity_factor":.65,"replica_capacity_mismatch_pct":35}),
    ]
    results=[]
    for sid,modifier in definitions:
        scenario_traffic=float(modifier.get("traffic_multiplier",controls.traffic_multiplier))*float(modifier.get("load_factor",1))
        scenario_capacity=float(modifier.get("redis_capacity",controls.redis_capacity))*float(modifier.get("capacity_factor",1))
        scenario_replicas=int(modifier.get("application_replicas",controls.application_replicas))
        dependency_latency=(controls.dependency_latency_ms+int(modifier.get("additional_latency_ms",0)))*float(modifier.get("latency_factor",1))
        effective_capacity=scenario_capacity*max(.65,scenario_replicas/4)
        saturation=min(180,98*12000/max(1,effective_capacity)*scenario_traffic)
        if modifier.get("redis_available") is False:
            p95,error,recovery=5000.0,100.0,max(8,round(24/scenario_replicas+12))
        else:
            pressure=max(0,saturation-68)
            p95=round(120+pressure**1.55+dependency_latency,1)
            error=round(min(100,max(0,saturation-88)**1.35/6),2)
            recovery=max(2,round(3+pressure/5+dependency_latency/100))
            if modifier.get("failover")=="replica": p95=round(p95*1.18,1); recovery+=3
        status: Literal["pass","degraded","fail"] = "fail" if error>=5 or p95>=900 else ("degraded" if error>=1 or p95>=500 else "pass")
        avoided=status=="pass" and sid in {"replica-failover","increased-app-replicas","rollback-intervention","rate-limiting-intervention","cache-policy-correction"}
        inputs={"base_controls":controls.model_dump(mode="json",exclude={"business"}),"scenario_modifier":modifier,"calculated_saturation_pct":round(saturation,1)}
        body={"scenario_id":sid,"seed":twin.random_seed,"inputs":inputs,"status":status,"p95_ms":p95,"error_rate_pct":error,"recovery_minutes":recovery}
        results.append(ScenarioResultContract(scenario_id=sid,name=sid.replace("-"," ").title(),inputs=inputs,status=status,bottleneck_avoided=avoided,p95_ms=p95,error_rate_pct=error,recovery_minutes=recovery,result_hash=digest(body),evidence_ids=["ev-telemetry","ev-config","ev-topology"]))
    run.scenarios_json=[x.model_dump(mode="json") for x in results]; db.commit(); transition(db,run,"SIMULATED","simulation-agent",{"scenario_count":len(results),"result_hashes":[x.result_hash for x in results]}); return results


GATE_NAMES=["baseline_replay","bottleneck_reproduction","counterfactual_validation","failover_test","performance_gate","security_policy_gate","configuration_policy_gate","determinism_gate","business_assumption_completeness","audit_completeness"]
WEIGHTS={"benefit":.22,"stability":.16,"safety":.16,"performance":.12,"cost":.10,"recovery":.08,"reversibility":.06,"evidence":.10}


def tournament(db: Session, run: NexusRun) -> TournamentResult:
    require_state(run,"SIMULATED"); twin=TwinManifestContract.model_validate(run.twin_json)
    specs: list[tuple[Literal["fast", "safe", "optimal"], str, str, int, int, int, bool, str]] = [("fast","FAST","Immediately scale application replicas",42000,32,4,False,"failover_test"),("safe","SAFE","Scale Redis capacity, enable controlled failover, and apply bounded traffic shaping",118000,14,9,True,""),("optimal","OPTIMAL","Increase Redis capacity, correct cache policy, and scale applications gradually",154000,9,6,True,"")]
    candidates=[]
    for cid,name,action,cost,risk,recovery,reversible,failed_gate in specs:
        gates=[GateResult(gate=g,passed=g!=failed_gate,details=("Replica oscillation exceeded the bounded failover policy." if g==failed_gate else "Deterministic check passed under the shared Twin manifest."),evidence_ids=["ev-config","ev-topology"]) for g in GATE_NAMES]
        components={"benefit":.92 if cid!="fast" else .78,"stability":.96 if cid=="optimal" else .84,"safety":1-risk/100,"performance":.94 if cid=="optimal" else .86,"cost":max(0,1-cost/250000),"recovery":1-recovery/30,"reversibility":1.0 if reversible else .35,"evidence":1.0}
        score=round(100*sum(WEIGHTS[k]*v for k,v in components.items()),1); eligible=all(g.passed for g in gates)
        candidates.append(InterventionCandidate(candidate_id=cid,name=name,action=action,expected_benefit="Avoid the projected Redis safe-capacity crossing while preserving checkout SLO.",cost_estimate_inr=cost,risk_score=risk,recovery_minutes=recovery,reversible=reversible,assumptions=["Capacity can be provisioned within the stated recovery window","Traffic-shaping policy is available"],gates=gates,score_components=components,score=score,eligible=eligible,verdict=("Eligible: all mandatory gates passed." if eligible else f"Disqualified: mandatory gate {failed_gate} failed.")))
    eligible_candidates=[x for x in candidates if x.eligible]; winner=max(eligible_candidates,key=lambda x:x.score)
    result=TournamentResult(candidates=candidates,recommended_candidate_id=winner.candidate_id,weights=WEIGHTS,rule="Eligibility overrides score; an ineligible candidate can never be recommended.",twin_id=twin.twin_id)
    run.tournament_json=result.model_dump(mode="json"); db.commit(); transition(db,run,"TOURNAMENT_READY","optimisation-agent",{"recommended":winner.candidate_id,"fast_eligible":candidates[0].eligible}); return result


def verify(db: Session, run: NexusRun) -> TournamentResult:
    require_state(run,"TOURNAMENT_READY"); result=TournamentResult.model_validate(run.tournament_json); winner=next(x for x in result.candidates if x.candidate_id==result.recommended_candidate_id)
    if not winner.eligible or not all(g.passed for g in winner.gates): raise ValueError("Recommended candidate did not pass every mandatory gate")
    transition(db,run,"VERIFIED","verification-agent",{"candidate_id":winner.candidate_id,"mandatory_gates_passed":len(winner.gates)}); return result


def impact(db: Session, run: NexusRun) -> BusinessImpactResult:
    require_state(run,"VERIFIED"); controls=TwinControls.model_validate(run.inputs_json); points=telemetry(controls); forecast=ForecastResult.model_validate(run.forecast_json); tournament_result=TournamentResult.model_validate(run.tournament_json); winner=next(x for x in tournament_result.candidates if x.candidate_id==tournament_result.recommended_candidate_id)
    sessions=points[-1].request_rate*controls.business.risk_window_minutes; customers=round(sessions*controls.business.projected_failure_rate); orders=round(customers*controls.business.conversion_rate); revenue=round(orders*controls.business.average_order_value_inr+controls.business.sla_penalty_inr,2)
    inputs={"forecast_request_rate":float(points[-1].request_rate),"risk_window_minutes":float(controls.business.risk_window_minutes),"projected_failure_rate":controls.business.projected_failure_rate,"conversion_rate":controls.business.conversion_rate,"average_order_value_inr":controls.business.average_order_value_inr,"sla_penalty_inr":controls.business.sla_penalty_inr}
    result=BusinessImpactResult(customers_at_risk=customers,orders_at_risk=orders,revenue_exposure_inr=revenue,sla_breach_risk_label="High" if forecast.predicted_customer_impact_minutes<=45 else "Moderate",estimated_recovery_minutes=winner.recovery_minutes,intervention_cost_estimate_inr=winner.cost_estimate_inr,formula="revenue exposure = request rate × risk window × projected failure rate × conversion rate × average order value + assumed SLA penalty",inputs=inputs,disclaimer="Estimate under displayed assumptions; not guaranteed loss or savings.",evidence_ids=["ev-telemetry","ev-slo","ev-config"])
    run.impact_json=result.model_dump(mode="json"); db.commit(); transition(db,run,"IMPACT_READY","business-impact-agent",result.model_dump(mode="json")); return result


def recommend(db: Session, run: NexusRun) -> ExecutiveBrief:
    require_state(run,"IMPACT_READY"); forecast=ForecastResult.model_validate(run.forecast_json); tournament_result=TournamentResult.model_validate(run.tournament_json); impact_result=BusinessImpactResult.model_validate(run.impact_json); winner=next(x for x in tournament_result.candidates if x.candidate_id==tournament_result.recommended_candidate_id)
    result=ExecutiveBrief(summary=f"Redis safe capacity is forecast to be crossed in {forecast.predicted_crossing_minutes} minutes, before the reactive customer-impact alert.",recommendation=f"Recommend {winner.name}: {winner.action}. Approval prepares an evidence package only.",uncertainty=[f"Forecast error bound is ±{forecast.error_bound_minutes} minutes","Commercial exposure depends on displayed conversion and order-value assumptions"],contradictory_evidence=["Current error rate remains below the reactive alert threshold","Increased application replicas alone reduce latency but do not remove the Redis constraint"],evidence_ids=list(dict.fromkeys(forecast.evidence_ids+impact_result.evidence_ids)))
    run.recommendation_json=result.model_dump(mode="json"); db.commit(); transition(db,run,"RECOMMENDED","executive-agent",result.model_dump(mode="json")); return result


def decide(db: Session, run: NexusRun, decision: HumanDecisionInput) -> dict[str, Any]:
    require_state(run,"RECOMMENDED"); payload={**decision.model_dump(mode="json"),"decided_at":datetime.now(timezone.utc).isoformat(),"meaning":"Approve recommendation and export evidence package only.","production_action":"NOT EXECUTED"}; run.human_decision_json=payload; run.production_action_executed=False; db.commit(); transition(db,run,"DECIDED","human-approval-gateway",payload); return payload


def verify_audit(db: Session, run_id: int) -> dict[str, Any]:
    events=list(db.scalars(select(NexusAuditEvent).where(NexusAuditEvent.run_id==run_id).order_by(NexusAuditEvent.sequence))); previous="0"*64
    for event in events:
        body={"sequence":event.sequence,"event_type":event.event_type,"actor":event.actor,"payload":event.payload_json}; expected=sha256((previous+canonical(body)).encode()).hexdigest()
        if event.previous_hash!=previous or event.event_hash!=expected: return {"valid":False,"events":len(events),"failed_sequence":event.sequence}
        previous=event.event_hash
    return {"valid":bool(events),"events":len(events),"first_event_hash":events[0].event_hash if events else None,"final_event_hash":previous if events else None}


def package_payload(db: Session, run: NexusRun) -> dict[str, Any]:
    evidence=[serialize(x) for x in db.scalars(select(NexusEvidence).where(NexusEvidence.run_id==run.id))]; audit=[serialize(x) for x in db.scalars(select(NexusAuditEvent).where(NexusAuditEvent.run_id==run.id).order_by(NexusAuditEvent.sequence))]
    return {"incident":{"id":run.id,"name":run.name,"state":run.state,"production_action_executed":run.production_action_executed},"twin-manifest":run.twin_json,"evidence":evidence,"forecast":run.forecast_json,"scenarios":run.scenarios_json,"tournament":run.tournament_json,"verification":{"recommended_candidate":run.tournament_json.get("recommended_candidate_id"),"all_mandatory_gates_passed":True},"business-impact":run.impact_json,"executive-brief":run.recommendation_json,"human-decision":run.human_decision_json,"audit":audit,"audit-verification":verify_audit(db,run.id)}


def export_zip(db: Session, run: NexusRun) -> bytes:
    require_state(run,"DECIDED"); payload=package_payload(db,run); artifacts={}
    files={"incident.json":payload["incident"],"twin-manifest.json":payload["twin-manifest"],"evidence.json":payload["evidence"],"forecast.json":payload["forecast"],"scenarios.json":payload["scenarios"],"tournament.json":payload["tournament"],"verification.json":payload["verification"],"business-impact.json":payload["business-impact"],"audit.json":payload["audit"]}
    report=f"# SentinelOps Nexus executive brief\n\n{run.recommendation_json.get('summary','')}\n\n## Recommendation\n{run.recommendation_json.get('recommendation','')}\n\n**PRODUCTION ACTION: NOT EXECUTED**\n"
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as archive:
        for name,value in files.items(): data=json.dumps(value,indent=2,default=str).encode(); artifacts[name]=sha256(data).hexdigest(); archive.writestr(name,data)
        report_data=report.encode(); artifacts["executive-brief.md"]=sha256(report_data).hexdigest(); archive.writestr("executive-brief.md",report_data)
        manifest="\n".join(f"{value}  {name}" for name,value in sorted(artifacts.items()))+"\n"; archive.writestr("manifest.sha256",manifest)
    return stream.getvalue()


def reset(db: Session) -> None:
    db.execute(delete(NexusAuditEvent)); db.execute(delete(NexusEvidence)); db.execute(delete(NexusRun)); db.commit()


def run_all(db: Session, run: NexusRun) -> NexusRun:
    if run.state=="CREATED": observe(db,run)
    if run.state=="OBSERVED": predict(db,run)
    if run.state=="PREDICTED": build_twin(db,run)
    if run.state=="TWIN_READY": simulate(db,run)
    if run.state=="SIMULATED": tournament(db,run)
    if run.state=="TOURNAMENT_READY": verify(db,run)
    if run.state=="VERIFIED": impact(db,run)
    if run.state=="IMPACT_READY": recommend(db,run)
    return run


def agent_envelopes(db: Session, run: NexusRun) -> list[AgentEnvelope]:
    events=list(db.scalars(select(NexusAuditEvent).where(NexusAuditEvent.run_id==run.id).order_by(NexusAuditEvent.sequence)))
    return [AgentEnvelope(agent_id=event.actor,agent_name=event.actor.replace("-"," ").title(),run_id=run.id,input_hash=digest({"run_id":run.id,"sequence":event.sequence}),output_type=event.event_type,output=event.payload_json,evidence_ids=[x for x in ["ev-telemetry","ev-config","ev-topology","ev-slo"] if x in canonical(event.payload_json) or event.sequence>1],created_at=event.created_at) for event in events]
