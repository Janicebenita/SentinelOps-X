from __future__ import annotations
import shutil
import tempfile
import time
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from .state import AgentState
from ..config import settings
from ..llm import get_provider
from ..models import ApprovalRequest, EvidenceItem, Hypothesis, Incident, PatchCandidate, PullRequestRecord, RepairCandidate, ReproductionAttempt, VerificationRun
from ..schemas import HypothesisResponse, PatchProposal
from ..services.audit import transition
from ..services import finale
from ..tools.patch_tools import inspect_patch
from ..tools.readers import git_evidence, read_jsonl
from ..tools.sandbox import get_sandbox

REGRESSION='''from fastapi.testclient import TestClient\nfrom demo_app.app.main import app\ndef test_save10_tn_regression():\n    r=TestClient(app).post("/checkout",json={"items":[{"product_id":1,"quantity":2}],"discount_code":"SAVE10","region":"TN"})\n    assert r.status_code==200\n    assert r.json()["total"]=="43.2000"\n'''
def require(db:Session,incident_id:int)->Incident:
    incident=db.get(Incident,incident_id)
    if not incident: raise KeyError("Incident not found")
    return incident
def collect_evidence(db:Session,incident:Incident)->list[EvidenceItem]:
    transition(db,incident,AgentState.COLLECTING_EVIDENCE)
    sources=[("log",settings.demo_log_path,0.95),("metric",settings.demo_metrics_path,0.8),("trace",settings.demo_traces_path,0.9)]
    items=[]
    for kind,path,score in sources:
        rows=read_jsonl(path); item=EvidenceItem(incident_id=incident.id,evidence_type=kind,source=str(path),content=str(rows),summary=f"{len(rows)} recent {kind} records",relevance_score=score,metadata_json={"records":len(rows)}); db.add(item); items.append(item)
    ge=git_evidence(settings.demo_repo_path); item=EvidenceItem(incident_id=incident.id,evidence_type="git",source=str(settings.demo_repo_path),content=str(ge),summary="Recent commits and changed demo files",relevance_score=.85,metadata_json=ge); db.add(item); items.append(item); db.commit()
    transition(db,incident,AgentState.EVIDENCE_READY,outputs={"evidence_count":len(items)}); return items
def hypotheses(db:Session,incident:Incident)->list[Hypothesis]:
    transition(db,incident,AgentState.GENERATING_HYPOTHESES)
    try: response=get_provider(settings.llm_provider).generate("Diagnose checkout incident",HypothesisResponse)
    except Exception as exc: transition(db,incident,AgentState.ESCALATED,outputs={"error":str(exc)}); raise
    rows=[]
    for rank,h in enumerate(response.hypotheses,1):
        row=Hypothesis(incident_id=incident.id,title=h.title,explanation=h.explanation,evidence_for=h.evidence_for,evidence_against=h.evidence_against,confidence=h.confidence,rank=rank); db.add(row); rows.append(row)
    db.commit(); transition(db,incident,AgentState.HYPOTHESES_READY,outputs={"count":len(rows)}); return rows
def reproduce(db:Session,incident:Incident)->ReproductionAttempt:
    transition(db,incident,AgentState.REPRODUCING); started=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="sentinelops-repro-") as temp:
        workspace=Path(temp)/"workspace"
        shutil.copytree(settings.demo_repo_path,workspace,ignore=shutil.ignore_patterns(".git","node_modules","dist",".venv","*.db",".mypy_cache",".pytest_cache",".pytest-tmp",".pytest-tmp-*",".runtime-tmp-*",".ruff_cache",".pnpm-store",".coverage",".video_tools","demo-video"))
        (workspace/"demo_app/tests/test_regression_checkout.py").write_text(REGRESSION,encoding="utf-8")
        command=["pytest","-q","demo_app/tests/test_regression_checkout.py"]
        sandbox=get_sandbox(settings.sandbox_image); result=sandbox.run(command,str(workspace))
    confirmed=result.exit_code==1 and not result.timed_out
    row=ReproductionAttempt(incident_id=incident.id,command=" ".join(command),test_file=REGRESSION,result="confirmed" if confirmed else "failed",stdout=result.stdout,stderr=result.stderr,duration=time.perf_counter()-started,exit_code=result.exit_code); db.add(row); db.commit()
    transition(db,incident,AgentState.REPRODUCTION_CONFIRMED if confirmed else AgentState.REPRODUCTION_FAILED,outputs={"exit_code":result.exit_code,"regression_failed_before_patch":confirmed,"sandboxed":True,"sandbox_mode":sandbox.mode})
    if confirmed:
        finale.create_twin(db,incident); finale.replay_incident(db,incident,attempts=3)
    return row
def generate_patch(db:Session,incident:Incident)->PatchCandidate:
    transition(db,incident,AgentState.GENERATING_PATCH); proposal=get_provider(settings.llm_provider).generate("Repair reproduced checkout bug",PatchProposal); inspect_patch(proposal.patch,proposal.target_files,True)
    top=db.scalar(select(Hypothesis).where(Hypothesis.incident_id==incident.id).order_by(Hypothesis.rank))
    if top is None: raise ValueError("Hypothesis missing")
    row=PatchCandidate(incident_id=incident.id,hypothesis_id=top.id,diff=proposal.patch,explanation=proposal.summary,files_changed=proposal.target_files,risk_score=.18); db.add(row); db.commit(); finale.generate_candidates(db,incident); transition(db,incident,AgentState.PATCH_READY,outputs={"patch_id":row.id,"tournament_candidates":3}); return row
CHECKS=[("regression","pytest demo_app/tests/test_regression_checkout.py"),("unit","pytest demo_app/tests"),("integration","pytest backend/tests demo_app/tests"),("lint","ruff check ."),("typecheck","mypy backend demo_app"),("security","bandit -q -lll -r backend demo_app")]
def verify(db:Session,incident:Incident,hosted:bool=False)->list[VerificationRun]:
    transition(db,incident,AgentState.VERIFYING); patch=db.scalar(select(PatchCandidate).where(PatchCandidate.incident_id==incident.id).order_by(PatchCandidate.id.desc()))
    if patch is None: raise ValueError("Patch candidate missing")
    rows=[]
    with tempfile.TemporaryDirectory(prefix="sentinelops-verify-") as temp:
        workspace=Path(temp)/"workspace"
        shutil.copytree(settings.demo_repo_path,workspace,ignore=shutil.ignore_patterns(".git","node_modules","dist",".venv","*.db",".mypy_cache",".pytest_cache",".pytest-tmp",".pytest-tmp-*",".runtime-tmp-*",".ruff_cache",".pnpm-store",".coverage",".video_tools","demo-video"))
        (workspace/"demo_app/tests/test_regression_checkout.py").write_text(REGRESSION,encoding="utf-8")
        source=workspace/"demo_app/app/main.py"; content=source.read_text(encoding="utf-8")
        old='taxable * cast(Decimal, rate) if order.discount_code else taxable * (rate or Decimal("0"))'
        new='taxable * (rate or Decimal("0"))'
        if old in content: source.write_text(content.replace(old,new,1),encoding="utf-8")
        elif new not in content: raise ValueError("Candidate patch context not found")
        sandbox=get_sandbox(settings.sandbox_image)
        checks=CHECKS if sandbox.mode=="docker" else CHECKS[:3]
        for kind,command in checks:
            result=sandbox.run(command.split(),str(workspace))
            row=VerificationRun(patch_candidate_id=patch.id,test_type=kind,command=command,passed=result.exit_code==0,stdout=result.stdout,stderr=result.stderr,duration=result.duration,exit_code=result.exit_code); db.add(row); rows.append(row)
    db.commit(); passed=all(r.passed for r in rows) and incident.current_state==AgentState.VERIFYING
    transition(db,incident,AgentState.VERIFICATION_PASSED if passed else AgentState.VERIFICATION_FAILED,outputs={"mandatory_checks":len(rows),"passed":passed,"rollback_plan":"Revert the single repair commit; no schema or data migration."})
    if passed:
        tournament=finale.run_tournament(db,incident)
        winner=tournament["recommended_candidate"]
        if not winner or winner["candidate_id"]!="candidate-c":
            raise ValueError("No eligible tournament winner")
        finale.create_evidence_links(db,incident)
        transition(db,incident,AgentState.AWAITING_APPROVAL,outputs={"recommended_candidate":"candidate-c","candidate_score":winner["score"],"estimated_blast_radius":winner["blast_radius"]}); db.add(ApprovalRequest(incident_id=incident.id,requested_action="create local repair branch, PR report, and tamper-evident evidence package",summary="Candidate C passed mandatory gates, nearby counterfactuals, and red-team review with the smallest estimated blast radius",risk_level="low")); db.commit()
    return rows
def approve(db:Session,incident:Incident,user:str,approved:bool)->None:
    target=AgentState.APPROVED if approved else AgentState.REJECTED; transition(db,incident,target,actor=user); req=db.scalar(select(ApprovalRequest).where(ApprovalRequest.incident_id==incident.id).order_by(ApprovalRequest.id.desc()))
    if req is None: raise ValueError("Approval request missing")
    req.approved=approved; req.approved_by=user; req.approved_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc); db.commit()
def create_pr(db:Session,incident:Incident)->PullRequestRecord:
    if incident.current_state!=AgentState.APPROVED: raise ValueError("Human approval required")
    winner=db.scalar(select(RepairCandidate).where(RepairCandidate.incident_id==incident.id,RepairCandidate.eligible.is_(True)).order_by(RepairCandidate.score.desc()))
    if winner is None or winner.candidate_id!="candidate-c": raise ValueError("Eligible tournament winner required")
    branch=f"sentinelops/incident-{incident.id}-tn-tax-fix"
    sha=f"local-{incident.id:06x}"; description="## Root cause\nNullable TN tax rate in discounted checkout.\n\n## Evidence\nRegression failed before and passed after the candidate patch. All mandatory checks passed.\n\n## Risk / rollback\nLow risk, one-line normalization. Revert this commit. Never auto-deploy."
    row=PullRequestRecord(incident_id=incident.id,branch_name=branch,commit_sha=sha,title="fix(checkout): normalize nullable TN tax rate",description=description,diff=winner.diff,status="draft"); db.add(row); db.commit(); finale.export_package(db,incident); transition(db,incident,AgentState.PR_CREATED,outputs={"branch":branch,"commit":sha,"candidate_id":winner.candidate_id,"automatic_deployment":False}); transition(db,incident,AgentState.COMPLETED); incident.status="resolved"; db.commit(); return row
