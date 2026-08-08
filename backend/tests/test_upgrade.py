from __future__ import annotations

import io
import zipfile

from sqlalchemy import select

from backend.app.auth import roles
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
    event_types={event["event_type"] for event in client.get(f"/api/v1/workflows/{run['id']}/timeline").json()}
    assert {"agent.opened","agent.run_requested","agent.run_completed","agent.rerun_requested"}.issubset(event_types)


def test_agent_execution_rejects_invalid_workflow_state_and_audits_failure(client,db):
    run=client.post("/api/v1/demo/seed").json()
    response=client.post(f"/api/v1/workflows/{run['id']}/agents/prediction-agent/run",json={"actor_name":"qa-lead"})
    assert response.status_code==409
    execution=db.scalar(select(AgentExecution).where(AgentExecution.workflow_id==run["id"],AgentExecution.agent_name=="prediction-agent"))
    assert execution is not None and execution.status=="FAILED" and "OBSERVED" in execution.error
    events=client.get(f"/api/v1/workflows/{run['id']}/agents/prediction-agent/events").json()
    assert any(event["event_type"]=="agent.run_failed" for event in events)


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
    events={event["event_type"] for event in client.get(f"/api/v1/workflows/{run['id']}/timeline").json()}
    assert {"approval.enabled","approval.submitted","state.decided"}.issubset(events)
    qualifications=db.scalars(select(VerificationRecord).where(VerificationRecord.workflow_id==run["id"],VerificationRecord.subject_type=="approver")).all()
    assert any(row.result=="MORE_INFORMATION_REQUIRED" and "mandatory_rationale" in row.failed_checks for row in qualifications)
    assert any(row.result=="VERIFIED" and row.checks.get("mandatory_rationale") for row in qualifications)


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


def test_role_token_is_regenerated_if_serialized_token_matches_demo_code(client,monkeypatch):
    original=roles._signed_role_token
    calls={"count":0}

    def collide_once(payload):
        calls["count"]+=1
        return "header.1111.signature" if calls["count"]==1 else original(payload)

    monkeypatch.setattr(roles,"_signed_role_token",collide_once)
    response=client.post("/api/v1/auth/verify-role",json={"actor_name":"Collision QA","access_code":"1111"})
    assert response.status_code==200
    assert "1111" not in response.text and "0000" not in response.text


def test_no_production_execution_endpoint_exists(client):
    paths=client.get("/openapi.json").json()["paths"]
    assert not any("execute-production" in path or "production-action" in path for path in paths)


def test_legacy_approval_is_also_role_protected(client):
    seeded=client.post("/api/demo/seed").json(); iid=seeded["ids"][0]
    client.post(f"/api/incidents/{iid}/start")
    intern=client.post("/api/v1/auth/verify-role",json={"actor_name":"Legacy Intern","access_code":"0000"}).json()
    blocked=client.post(f"/api/incidents/{iid}/approve",json={"approved_by":"Legacy Intern","rationale":"Evidence reviewed.","verification_token":intern["verification_token"]})
    assert blocked.status_code==403 and blocked.json()["code"]=="APPROVER_NOT_QUALIFIED"
    missing_rationale=client.post(f"/api/incidents/{iid}/approve",json={"approved_by":"Legacy Intern","verification_token":intern["verification_token"]})
    assert missing_rationale.status_code==422


def test_codes_never_reach_logs_database_audit_or_evidence_export(client,db,caplog):
    run=ready_run(client)
    senior=client.post("/api/v1/auth/verify-role",json={"actor_name":"Release Reviewer","access_code":"1111"}).json()
    approval=client.post(f"/api/v1/workflows/{run['id']}/approve",json={"actor_name":"Release Reviewer","decision":"approve","rationale":"Release evidence and every mandatory gate were reviewed.","verification_token":senior["verification_token"]})
    assert approval.status_code==200
    exported=client.get(f"/api/v1/workflows/{run['id']}/export")
    assert exported.status_code==200
    assert b"0000" not in exported.content and b"1111" not in exported.content
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        assert archive.testzip() is None
        assert {"audit.json","verification.json","manifest.sha256"}.issubset(archive.namelist())
        archive_payload=b"".join(archive.read(name) for name in archive.namelist())
        assert b'"0000"' not in archive_payload and b'"1111"' not in archive_payload
        assert b'"access_code"' not in archive_payload
    rows=db.scalars(select(RoleVerification)).all()
    persisted_values=[value for row in rows for key,value in row.__dict__.items() if not key.startswith("_sa_")]
    assert "0000" not in persisted_values and "1111" not in persisted_values
    assert "0000" not in caplog.text and "1111" not in caplog.text
    assert client.get(f"/api/v1/audit/verify?run_id={run['id']}").json()["valid"] is True
