from __future__ import annotations

from sqlalchemy import select

from backend.app.config import settings
from backend.app.models import AgentExecution, HumanDecision, RoleVerification, VerificationRecord


def ready_run(client):
    run=client.post("/api/v1/demo/seed").json()
    return client.post(f"/api/v1/workflows/{run['id']}/run-all").json()


def test_all_agents_are_listed_clickable_and_operational(client,db):
    run=ready_run(client); agents=client.get("/api/v1/agents").json()
    required={"nexus-orchestrator","observer-agent","evidence-agent","process-discovery-agent","prediction-agent","digital-twin-agent","simulation-agent","optimization-agent","verification-agent","business-impact-agent","executive-agent"}
    assert {x["agent_name"] for x in agents}==required
    for name in required:
        assert client.get(f"/api/v1/workflows/{run['id']}/agents/{name}").status_code==200
        assert client.post(f"/api/v1/workflows/{run['id']}/agents/{name}/run",json={"actor_name":"qa-lead"}).status_code==200
        assert client.post(f"/api/v1/workflows/{run['id']}/agents/{name}/rerun",json={"actor_name":"qa-lead"}).status_code==200
        assert client.get(f"/api/v1/workflows/{run['id']}/agents/{name}/events").status_code==200
    assert len(db.scalars(select(AgentExecution).where(AgentExecution.workflow_id==run["id"])).all())==22


def test_role_mapping_intern_block_and_senior_approval(client,db):
    run=ready_run(client)
    intern=client.post("/api/v1/auth/verify-role",json={"actor_name":"Intern User","access_code":"0000"})
    assert intern.status_code==200 and intern.json()["role"]=="INTERN" and "approve" not in intern.json()["permissions"]
    blocked=client.post(f"/api/v1/workflows/{run['id']}/approve",json={"actor_name":"Intern User","decision":"approve","rationale":"I reviewed the evidence.","verification_token":intern.json()["verification_token"]})
    assert blocked.status_code==403 and blocked.json()["code"]=="APPROVER_NOT_QUALIFIED"
    senior=client.post("/api/v1/auth/verify-role",json={"actor_name":"Senior User","access_code":"1111"})
    assert senior.status_code==200 and senior.json()["role"]=="SENIOR_DEVELOPER"
    approved=client.post(f"/api/v1/workflows/{run['id']}/approve",json={"actor_name":"Senior User","decision":"approve","rationale":"All mandatory gates and evidence references were reviewed.","verification_token":senior.json()["verification_token"]})
    assert approved.status_code==200 and approved.json()["production_action"]=="NOT EXECUTED"
    assert db.scalar(select(HumanDecision).where(HumanDecision.workflow_id==run["id"])).actor_role=="SENIOR_DEVELOPER"


def test_invalid_and_expired_tokens_fail_safely(client,monkeypatch):
    run=ready_run(client)
    invalid=client.post("/api/v1/auth/verify-role",json={"actor_name":"Unknown User","access_code":"9999"})
    assert invalid.status_code==401 and invalid.json()["code"]=="INVALID_ACCESS_CODE"
    monkeypatch.setattr(settings,"role_token_expiry_minutes",-1)
    expired=client.post("/api/v1/auth/verify-role",json={"actor_name":"Senior User","access_code":"1111"}).json()
    denied=client.post(f"/api/v1/workflows/{run['id']}/approve",json={"actor_name":"Senior User","decision":"approve","rationale":"Reviewed evidence.","verification_token":expired["verification_token"]})
    assert denied.status_code==401 and denied.json()["code"]=="ROLE_TOKEN_EXPIRED"


def test_verification_persists_and_plaintext_codes_never_persist_or_return(client,db):
    run=ready_run(client)
    result=client.post(f"/api/v1/workflows/{run['id']}/verification/run").json()
    assert result["result"]=="VERIFIED" and result["checks"]["production_execution_disabled"] is True
    assert db.scalar(select(VerificationRecord).where(VerificationRecord.workflow_id==run["id"])) is not None
    response=client.post("/api/v1/auth/verify-role",json={"actor_name":"Security QA","access_code":"1111"})
    assert "1111" not in response.text and "0000" not in response.text
    rows=db.scalars(select(RoleVerification)).all()
    assert all(row.code_fingerprint not in {"0000","1111"} for row in rows)


def test_no_production_execution_endpoint_exists(client):
    paths=client.get("/openapi.json").json()["paths"]
    assert not any("execute-production" in path or "production-action" in path for path in paths)
