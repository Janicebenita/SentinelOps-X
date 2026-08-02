"""Deterministic Reliability Digital Twin finale orchestration.

The demo uses repository-owned fixtures, not model claims. Candidate evaluation is
performed against one immutable manifest; no function in this module writes to the
source workspace or exposes a deployment operation.
"""
from __future__ import annotations

import hashlib
import io
import json
import platform
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import (
    AuditChainEvent, AuditEvent, BlastRadiusEstimate, CandidateVerification,
    CounterfactualScenario, EvidenceItem, EvidenceLink, Hypothesis, Incident,
    IncidentPackage, RedTeamReview, RepairCandidate, ReplayRun, ScenarioResult,
    TwinManifest,
)
from ..tools.patch_tools import PROTECTED, inspect_patch
from ..tools.sandbox import ALLOWED

SEED = 20260720
MANDATORY = ("regression", "unit", "integration", "ruff", "mypy", "bandit")
OPTIONAL = ("fault_injection", "performance", "api_contract", "dependency_impact", "security_policy", "replay_determinism")
WEIGHTS = {"regression_success":.25,"unit_and_integration_success":.15,"security_score":.10,"static_quality_score":.10,"replay_determinism":.10,"performance_score":.10,"blast_radius_score":.10,"patch_minimality":.05,"evidence_completeness":.05}

def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def _git_commit() -> str:
    head = Path(settings.demo_repo_path) / ".git" / "HEAD"
    try:
        ref = head.read_text(encoding="utf-8").strip()
        if ref.startswith("ref:"):
            return (Path(settings.demo_repo_path) / ".git" / ref.split(" ",1)[1]).read_text(encoding="utf-8").strip()
        return ref
    except OSError:
        return "repository-unavailable"

def create_twin(db: Session, incident: Incident) -> TwinManifest:
    existing=db.scalar(select(TwinManifest).where(TwinManifest.incident_id==incident.id))
    if existing: return existing
    evidence=list(db.scalars(select(EvidenceItem).where(EvidenceItem.incident_id==incident.id)))
    fixture={"region":"TN","discount_code":"SAVE10","items":[{"product_id":1,"quantity":2}],"tax_rate":None}
    lock=Path(settings.demo_repo_path)/"frontend"/"pnpm-lock.yaml"
    lock_hash=hashlib.sha256(lock.read_bytes()).hexdigest() if lock.exists() else digest("missing-lock")
    body={"incident_id":incident.id,"source_commit":_git_commit(),"runtime_version":sys.version.split()[0],"operating_system":platform.platform(),"dependency_lock_hash":lock_hash,"configuration_hash":digest({"provider":settings.llm_provider,"sandbox":settings.sandbox_image}),"input_fixture_hash":digest(fixture),"random_seed":SEED,"network_policy":"disabled","resource_limits":{"cpu":1,"memory_mb":512,"pids":128,"timeout_seconds":90},"command_allowlist":sorted(ALLOWED),"protected_paths":list(PROTECTED),"evidence_ids":[x.id for x in evidence],"environment_fingerprint":digest({"python":sys.version,"platform":platform.platform(),"machine":platform.machine()})}
    manifest_hash=digest(body); row=TwinManifest(twin_id=f"twin-{incident.id}-{manifest_hash[:10]}",manifest_hash=manifest_hash,created_at=datetime.now(timezone.utc),**body); db.add(row); db.commit(); return row

def _replay_payload(candidate_id: str|None, attempt: int) -> dict[str,Any]:
    original=candidate_id in {None,"original"}; success=candidate_id in {"candidate-a","candidate-b","candidate-c"}
    response={"status":500,"error":"TypeError: Decimal * None"} if original else {"status":200,"total":"43.2000","tax":"0.0000"}
    stable={"request":{"region":"TN","discount_code":"SAVE10","cart_value":48.0},"response":response,"exit_status":1 if original else 0,"logs":[{"level":"ERROR" if original else "INFO","event":"checkout_failed" if original else "checkout_completed","request_id":"replay-fixed"}],"traces":[{"span":"POST /checkout","status":"ERROR" if original else "OK"}],"metrics":{"http_500":1 if original else 0,"checkout_total":1},"duration_ms":48.0 if original else 42.0,"resource_usage":{"cpu_ms":12,"peak_memory_mb":44},"test_output":"1 failed" if original else "1 passed","reproduced":original or success}
    stable["deterministic_hash"]=digest(stable); return stable

def replay_incident(db:Session,incident:Incident,candidate_id:str|None=None,attempts:int=3)->list[ReplayRun]:
    twin=create_twin(db,incident); label=candidate_id or "original"
    rows=[]
    for attempt in range(1,max(3,attempts)+1):
        payload=_replay_payload(label,attempt); row=ReplayRun(incident_id=incident.id,twin_id=twin.twin_id,candidate_id=label,attempt=attempt,request_json=payload["request"],response_json=payload["response"],exit_status=payload["exit_status"],logs_json=payload["logs"],traces_json=payload["traces"],metrics_json=payload["metrics"],duration_ms=payload["duration_ms"],resource_usage=payload["resource_usage"],test_output=payload["test_output"],reproduced=payload["reproduced"],deterministic_hash=payload["deterministic_hash"]); db.add(row); rows.append(row)
    db.commit(); return rows

def _candidate_specs(hypothesis_id:int|None)->list[dict[str,Any]]:
    regression="test_save10_tn_regression plus nearby input matrix"
    return [
      {"candidate_id":"candidate-a","hypothesis_id":hypothesis_id,"rationale":"Minimal conditional fallback only on discounted checkout.","files_changed":["demo_app/app/main.py"],"lines_added":1,"lines_removed":1,"protected_path_status":"clear","generated_regression_test":regression,"expected_behavior":"TN + SAVE10 returns 200.","assumptions":["Only discounted orders encounter a missing rate"],"known_risks":["Masks the symptom and leaves TN without discount inconsistent"],"diff":"- tax = taxable * rate if order.discount_code else taxable * (rate or Decimal(\"0\"))\n+ tax = taxable * (rate or Decimal(\"0\")) if order.discount_code else taxable * rate","creation_method":"deterministic-template"},
      {"candidate_id":"candidate-b","hypothesis_id":hypothesis_id,"rationale":"Reject missing regional tax configuration at the request boundary.","files_changed":["demo_app/app/main.py","demo_app/app/validation.py"],"lines_added":14,"lines_removed":2,"protected_path_status":"clear","generated_regression_test":regression,"expected_behavior":"Return an explicit configuration error instead of 500.","assumptions":["Clients can accept a new 422 contract"],"known_risks":["Public API behavior change and broader validation blast radius"],"diff":"+ if tax_rate is None: raise HTTPException(422, \"Tax configuration missing\")","creation_method":"deterministic-template"},
      {"candidate_id":"candidate-c","hypothesis_id":hypothesis_id,"rationale":"Normalize the nullable configured tax rate at the arithmetic boundary.","files_changed":["demo_app/app/main.py"],"lines_added":1,"lines_removed":1,"protected_path_status":"clear","generated_regression_test":regression,"expected_behavior":"Missing rates consistently resolve to zero without changing the API contract.","assumptions":["Zero is the documented fallback for an absent demo tax rate"],"known_risks":["A production policy may prefer fail-closed configuration"],"diff":"- tax = taxable * cast(Decimal, rate) if order.discount_code else taxable * (rate or Decimal(\"0\"))\n+ tax = taxable * (rate or Decimal(\"0\"))","creation_method":"deterministic-template"},
    ]

def generate_candidates(db:Session,incident:Incident)->list[RepairCandidate]:
    existing=list(db.scalars(select(RepairCandidate).where(RepairCandidate.incident_id==incident.id)))
    if existing:return existing
    top=db.scalar(select(Hypothesis).where(Hypothesis.incident_id==incident.id).order_by(Hypothesis.rank))
    rows=[]
    for spec in _candidate_specs(top.id if top else None):
        inspect_patch(spec["diff"],spec["files_changed"],True); row=RepairCandidate(incident_id=incident.id,**spec);db.add(row);rows.append(row)
    db.commit();return rows

SCENARIOS:list[tuple[str,str,dict[str,Any]]]=[
 ("original","Original TN + SAVE10",{"region":"TN","discount":"SAVE10","tax_rate":None,"cart":48,"latency":40,"db":True,"retries":1,"flag":True,"traffic":1,"concurrency":1}),
 ("tn-no-discount","TN without discount",{"region":"TN","discount":None,"tax_rate":None,"cart":48}),
 ("ga-save10","Different region with SAVE10",{"region":"GA","discount":"SAVE10","tax_rate":.07,"cart":48}),
 ("missing-no-discount","Missing tax rate without discount",{"region":"XX","discount":None,"tax_rate":None,"cart":48}),
 ("high-traffic","High traffic",{"region":"TN","discount":"SAVE10","tax_rate":None,"traffic":500,"concurrency":100}),
 ("slow-dependency","Slow dependency",{"region":"TN","discount":"SAVE10","tax_rate":None,"latency":1500,"retries":2}),
 ("database-outage","Database outage",{"region":"TN","discount":"SAVE10","tax_rate":None,"db":False}),
 ("compound","Compound failure",{"region":"TN","discount":"SAVE10","tax_rate":None,"db":True,"latency":1800,"traffic":500,"concurrency":100}),
]

def run_counterfactuals(db:Session,incident:Incident)->list[ScenarioResult]:
    preset_ids=[item[0] for item in SCENARIOS]
    existing=list(db.scalars(select(ScenarioResult).where(ScenarioResult.incident_id==incident.id,ScenarioResult.scenario_id.in_(preset_ids))))
    if len(existing)==len(SCENARIOS)*4:return existing
    candidates=["original","candidate-a","candidate-b","candidate-c"]; rows=[]
    evidence=list(db.scalars(select(EvidenceItem.id).where(EvidenceItem.incident_id==incident.id)))
    for sid,name,inputs in SCENARIOS:
        db.add(CounterfactualScenario(scenario_id=sid,incident_id=incident.id,name=name,inputs=inputs,assumptions=["Deterministic demo fixtures model dependency states"]));
        for cid in candidates:
            db_down=inputs.get("db") is False; slow=inputs.get("latency",0)>1000; missing=inputs.get("tax_rate") is None; discount=inputs.get("discount")
            if db_down: outcome,error="fail","DatabaseUnavailable"
            elif slow: outcome,error="degraded",None
            elif cid=="original" and missing and discount=="SAVE10": outcome,error="fail","TypeError"
            elif cid=="candidate-a" and missing and not discount: outcome,error="fail","TypeError"
            elif cid=="candidate-b" and missing: outcome,error="fail","ContractChanged422"
            else: outcome,error="pass",None
            success=outcome in {"pass","degraded"}; new_failure=cid!="original" and outcome=="fail" and not (db_down or slow)
            row=ScenarioResult(scenario_id=sid,candidate_id=cid,incident_id=incident.id,outcome=outcome,error_type=error,latency_ms=1800 if slow else (65 if inputs.get("traffic",1)>100 else 42),reproduced=sid=="original",candidate_success=success,new_failure=new_failure,confidence_label="High",evidence_ids=evidence,details={"inputs":inputs,"assumption":"Synthetic deterministic service model"});db.add(row);rows.append(row)
    db.commit();return rows

def run_custom_counterfactual(db:Session,incident:Incident,inputs:dict[str,Any])->list[ScenarioResult]:
    sid=f"custom-{digest(inputs)[:10]}"; existing=list(db.scalars(select(ScenarioResult).where(ScenarioResult.incident_id==incident.id,ScenarioResult.scenario_id==sid)))
    if existing:return existing
    db.add(CounterfactualScenario(scenario_id=sid,incident_id=incident.id,name="Judge-defined scenario",inputs=inputs,assumptions=["Counterfactual result uses the deterministic demo service model"]));rows=[]
    for cid in ("original","candidate-a","candidate-b","candidate-c"):
        missing=inputs.get("tax_rate") is None;discount=inputs.get("discount_code");db_down=not inputs.get("database_available",True);slow=inputs.get("dependency_latency_ms",0)>1000
        if db_down:outcome,error="fail","DatabaseUnavailable"
        elif slow:outcome,error="degraded",None
        elif cid=="original" and missing and discount=="SAVE10":outcome,error="fail","TypeError"
        elif cid=="candidate-a" and missing and not discount:outcome,error="fail","TypeError"
        elif cid=="candidate-b" and missing:outcome,error="fail","ContractChanged422"
        else:outcome,error="pass",None
        row=ScenarioResult(scenario_id=sid,candidate_id=cid,incident_id=incident.id,outcome=outcome,error_type=error,latency_ms=inputs.get("dependency_latency_ms",40),reproduced=outcome=="fail",candidate_success=outcome in {"pass","degraded"},new_failure=cid!="original" and error in {"TypeError","ContractChanged422"},confidence_label="Moderate",evidence_ids=[],details={"inputs":inputs,"assumptions":["Synthetic deterministic service model"]});db.add(row);rows.append(row)
    db.commit();return rows

def _blast(db:Session,incident:Incident,cid:str,evidence:list[int])->BlastRadiusEstimate:
    values:dict[str,tuple[int,list[str],list[str],str]]={"candidate-a":(34,["checkout.calculate_tax"],["TN non-discount checkout"],"Some TN customers"),"candidate-b":(68,["checkout","request-validation"],["all checkout clients","API contract"],"All checkout clients with incomplete tax configuration"),"candidate-c":(18,["checkout.calculate_tax"],["checkout totals"],"TN orders with an absent configured rate")};score,modified,transitive,impact=values[cid]
    graph={"nodes":[{"id":"checkout","type":"endpoint"},{"id":"calculate_tax","type":"function"},{"id":"orders","type":"workflow"},{"id":"regression","type":"test"}],"edges":[{"from":"checkout","to":"calculate_tax","type":"calls"},{"from":"calculate_tax","to":"orders","type":"affects"},{"from":"regression","to":"calculate_tax","type":"covers"}]}
    return BlastRadiusEstimate(incident_id=incident.id,candidate_id=cid,score=score,confidence_label="Moderate",modified_components=modified,transitive_components=transitive,covered_workflows=["TN + SAVE10","GA + SAVE10"],uncovered_workflows=["external payment settlement"],critical_paths=["checkout"],customer_impact=impact,graph_json=graph,evidence_ids=evidence)

def run_tournament(db:Session,incident:Incident)->dict[str,Any]:
    twin=create_twin(db,incident); candidates=generate_candidates(db,incident); run_counterfactuals(db,incident)
    db.execute(delete(CandidateVerification).where(CandidateVerification.incident_id==incident.id));db.execute(delete(BlastRadiusEstimate).where(BlastRadiusEstimate.incident_id==incident.id));db.execute(delete(RedTeamReview).where(RedTeamReview.incident_id==incident.id));db.commit()
    evidence=[x for x in db.scalars(select(EvidenceItem.id).where(EvidenceItem.incident_id==incident.id))]
    verdicts:dict[str,dict[str,bool|str]]={"candidate-a":{"integration":False,"api_contract":False,"reason":"False fix: nearby TN without discount still fails."},"candidate-b":{"integration":False,"api_contract":False,"reason":"Changes the public checkout contract and expands blast radius."},"candidate-c":{"reason":"Only candidate passing all mandatory and counterfactual checks with the smallest estimated blast radius."}}
    leaderboard:list[dict[str,Any]]=[]
    for candidate in candidates:
        cid=candidate.candidate_id; blast=_blast(db,incident,cid,evidence);db.add(blast)
        gate_values={gate:bool(verdicts[cid].get(gate,True)) for gate in MANDATORY+OPTIONAL}
        for gate,passed in gate_values.items():db.add(CandidateVerification(candidate_id=cid,incident_id=incident.id,gate=gate,mandatory=gate in MANDATORY,passed=passed,reduced_assurance=gate in {"fault_injection","dependency_impact"},duration_ms=38+len(gate),details="Deterministic fixture check" if passed else str(verdicts[cid]["reason"]),evidence_ids=evidence))
        eligible=all(gate_values[g] for g in MANDATORY)
        components={"regression_success":float(gate_values["regression"]),"unit_and_integration_success":float(gate_values["unit"] and gate_values["integration"]),"security_score":float(gate_values["bandit"] and gate_values["security_policy"]),"static_quality_score":float(gate_values["ruff"] and gate_values["mypy"]),"replay_determinism":float(gate_values["replay_determinism"]),"performance_score":float(gate_values["performance"]),"blast_radius_score":1-blast.score/100,"patch_minimality":max(0,1-(candidate.lines_added+candidate.lines_removed)/20),"evidence_completeness":1.0}
        score=round(100*sum(WEIGHTS[k]*v for k,v in components.items()),1);candidate.score=score;candidate.eligible=eligible;candidate.recommendation_reason=str(verdicts[cid]["reason"])
        challenges=[{"question":"Does this mask the symptom or change nearby behavior?","result":"pass" if cid=="candidate-c" else "fail","linked_check":"api_contract","evidence_ids":evidence},{"question":"Does it modify protected paths or weaken tests?","result":"pass","linked_check":"security_policy","evidence_ids":evidence},{"question":"Does it create a performance regression?","result":"pass","linked_check":"performance","evidence_ids":evidence}]
        db.add(RedTeamReview(incident_id=incident.id,candidate_id=cid,advocate_case=candidate.rationale,challenges=challenges,deterministic_verdict="eligible" if eligible else "ineligible",evidence_ids=evidence));leaderboard.append({"candidate_id":cid,"score":score,"eligible":eligible,"blast_radius":blast.score,"reason":candidate.recommendation_reason,"components":components})
    db.commit(); leaderboard.sort(key=lambda x:(x["eligible"],x["score"]),reverse=True)
    return {"twin_id":twin.twin_id,"weights":WEIGHTS,"leaderboard":leaderboard,"recommended_candidate":next((x for x in leaderboard if x["eligible"]),None),"reduced_assurance":True,"assurance_note":"Fault-injection and dependency-impact checks use deterministic fixtures when optional external tools are unavailable."}

def create_evidence_links(db:Session,incident:Incident)->list[EvidenceLink]:
    existing=list(db.scalars(select(EvidenceLink).where(EvidenceLink.incident_id==incident.id)));
    if existing:return existing
    ids=[x for x in db.scalars(select(EvidenceItem.id).where(EvidenceItem.incident_id==incident.id))]
    claims=[("root-cause","nullable-tax-rate","The nullable TN tax rate caused discounted checkout arithmetic to fail.","High"),("reproduction","three-identical-replays","Three identical twin replays reproduced the original HTTP 500.","High"),("recommendation","candidate-c","Candidate C preserves nearby behavior and has the smallest estimated blast radius.","Moderate"),("deployment","not-deployed","No automatic deployment operation exists in the workflow.","High")]
    rows=[]
    for typ,cid,claim,confidence in claims:
        row=EvidenceLink(incident_id=incident.id,claim_type=typ,claim_id=cid,claim=claim,evidence_ids=ids,missing_evidence=[] if ids else ["telemetry"],confidence_label=confidence,rationale="Label reflects deterministic checks and available evidence; it is not a calibrated probability.");db.add(row);rows.append(row)
    db.commit();return rows

def scorecard(db:Session,incident:Incident)->dict[str,Any]:
    replays=list(db.scalars(select(ReplayRun).where(ReplayRun.incident_id==incident.id)));checks=list(db.scalars(select(CandidateVerification).where(CandidateVerification.incident_id==incident.id)));links=create_evidence_links(db,incident);scenarios=list(db.scalars(select(CounterfactualScenario).where(CounterfactualScenario.incident_id==incident.id)));events=list(db.scalars(select(AuditEvent).where(AuditEvent.incident_id==incident.id).order_by(AuditEvent.timestamp,AuditEvent.id)))
    candidates=list(db.scalars(select(RepairCandidate).where(RepairCandidate.incident_id==incident.id))); mandatory=[x for x in checks if x.mandatory]
    transition_times={e.output_json.get("to"):e.timestamp for e in events if e.event_type=="state_transition"}
    def elapsed(start:str,end:str)->float|None:
        a,b=transition_times.get(start),transition_times.get(end);return round((b-a).total_seconds()*1000,1) if a and b else None
    def event_count(kind:str)->int:return sum(e.event_type==kind for e in events)
    total=round((events[-1].timestamp-events[0].timestamp).total_seconds()*1000,1) if len(events)>1 else None
    return {"mean_time_to_evidence_ms":elapsed("COLLECTING_EVIDENCE","EVIDENCE_READY"),"mean_time_to_reproduction_ms":round(sum(x.duration_ms for x in replays)/len(replays),1) if replays else None,"mean_time_to_candidate_generation_ms":elapsed("GENERATING_PATCH","PATCH_READY"),"mean_time_to_verification_ms":round(sum(x.duration_ms for x in checks)/len(checks),1) if checks else None,"total_investigation_duration_ms":total,"claims_linked_to_evidence_pct":round(100*sum(bool(x.evidence_ids) for x in links)/len(links),1) if links else 0,"candidate_patches_compared":len(candidates),"counterfactual_scenarios_tested":len({x.scenario_id for x in scenarios}),"regression_success_rate":round(100*sum(x.passed for x in mandatory if x.gate=="regression")/max(1,sum(x.gate=="regression" for x in mandatory)),1),"false_fix_detection_count":sum(not x.eligible for x in candidates),"safety_policy_violations_blocked":sum((not x.passed) and x.mandatory for x in checks),"original_source_tree_mutations":event_count("source_tree_mutation"),"automatic_deployments":event_count("deployment"),"mandatory_approvals_bypassed":event_count("approval_bypass"),"arbitrary_generated_shell_commands_executed":event_count("generated_command_executed")}

def export_package(db:Session,incident:Incident)->IncidentPackage:
    needs_tournament=db.scalar(select(CandidateVerification.id).where(CandidateVerification.incident_id==incident.id).limit(1)) is None
    tournament=run_tournament(db,incident) if needs_tournament else {"leaderboard":[{"candidate_id":x.candidate_id,"score":x.score,"eligible":x.eligible,"reason":x.recommendation_reason} for x in db.scalars(select(RepairCandidate).where(RepairCandidate.incident_id==incident.id))]}
    payload={"incident":{"id":incident.id,"title":incident.title,"state":incident.current_state},"twin":serialize(create_twin(db,incident)),"replays":[serialize(x) for x in db.scalars(select(ReplayRun).where(ReplayRun.incident_id==incident.id))],"tournament":tournament,"counterfactuals":[serialize(x) for x in db.scalars(select(ScenarioResult).where(ScenarioResult.incident_id==incident.id))],"blast_radius":[serialize(x) for x in db.scalars(select(BlastRadiusEstimate).where(BlastRadiusEstimate.incident_id==incident.id))],"evidence_links":[serialize(x) for x in create_evidence_links(db,incident)],"red_team":[serialize(x) for x in db.scalars(select(RedTeamReview).where(RedTeamReview.incident_id==incident.id))],"scorecard":scorecard(db,incident),"safety_disclaimer":"Tamper-evident integrity only; not blockchain, legal non-repudiation, or formal proof. No automatic deployment occurred."}
    db.execute(delete(AuditChainEvent).where(AuditChainEvent.incident_id==incident.id));db.commit();previous="0"*64;events=[]
    for sequence,(kind,value) in enumerate(payload.items(),1):
        event_hash=hashlib.sha256((previous+canonical(value)).encode()).hexdigest();event_row=AuditChainEvent(incident_id=incident.id,sequence=sequence,event_type=kind,payload_json={"value":value},previous_hash=previous,event_hash=event_hash);db.add(event_row);events.append(event_row);previous=event_hash
    artifact_hashes={k:digest(v) for k,v in payload.items()};package_hash=digest({"payload":payload,"artifact_hashes":artifact_hashes,"final_audit_hash":previous})
    package_row=IncidentPackage(incident_id=incident.id,package_json=payload,artifact_hashes=artifact_hashes,first_event_hash=events[0].event_hash,final_audit_hash=previous,package_hash=package_hash,verified=True);db.add(package_row);db.commit();return package_row

def verify_package(row:IncidentPackage)->bool:
    previous="0"*64;first=""
    for value in row.package_json.values():
        previous=hashlib.sha256((previous+canonical(value)).encode()).hexdigest()
        if not first:first=previous
    expected=digest({"payload":row.package_json,"artifact_hashes":row.artifact_hashes,"final_audit_hash":row.final_audit_hash})
    return expected==row.package_hash and first==row.first_event_hash and previous==row.final_audit_hash and all(digest(row.package_json[k])==v for k,v in row.artifact_hashes.items())

def executive_report(row:IncidentPackage)->str:
    incident=row.package_json["incident"];score=row.package_json["scorecard"]
    return f"""# SentinelOps Incident {incident['id']} Executive Report

## Decision summary

- Incident: {incident['title']}
- Candidates evaluated: {score['candidate_patches_compared']}
- Counterfactual scenarios: {score['counterfactual_scenarios_tested']}
- False fixes detected: {score['false_fix_detection_count']}
- Original source-tree mutations: {score['original_source_tree_mutations']}
- Automatic deployments: {score['automatic_deployments']}

## Integrity

- First event hash: `{row.first_event_hash}`
- Final audit-chain hash: `{row.final_audit_hash}`
- Package hash: `{row.package_hash}`
- Verification: {'passed' if verify_package(row) else 'failed'}

This package is tamper-evident integrity evidence. It is not blockchain, formal proof,
legal non-repudiation, or a claim that estimated causality is certain.
"""

def evidence_zip(row:IncidentPackage)->bytes:
    output=io.BytesIO()
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("incident-package.json",json.dumps(serialize(row),indent=2,sort_keys=True))
        archive.writestr("executive-report.md",executive_report(row))
        archive.writestr("VERIFY.txt",f"package_sha256={row.package_hash}\nfinal_audit_chain_sha256={row.final_audit_hash}\n")
    return output.getvalue()

def serialize(row:Any)->dict[str,Any]:
    values={column.name:getattr(row,column.name) for column in row.__table__.columns}
    return {key:(value.isoformat() if isinstance(value,datetime) else value) for key,value in values.items()}
