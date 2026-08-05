from datetime import timedelta

from backend.app.enterprise.contracts import A2AMessage, EventEnvelope, utcnow
from backend.app.models import A2AMessageRecord, IntegrationInvocation

AUTH={"Authorization":"Bearer development-integration-token"}

def ready_run(client):
    run=client.post("/api/v1/demo/seed").json()
    return client.post(f"/api/v1/workflows/{run['id']}/run-all").json()

def test_dynamic_integration_status(client):
    response=client.get("/api/v1/platform/integrations")
    assert response.status_code==200
    statuses={x["integration"]:x["status"] for x in response.json()}
    assert statuses["A2A"]=="IMPLEMENTED_AND_VERIFIED"
    assert statuses["Antigravity"]=="DOCUMENTATION_UNAVAILABLE"
    assert all(x["production_action"]=="NOT_EXECUTED" for x in response.json())

def test_event_idempotency_and_auth(client):
    run=ready_run(client); event=EventEnvelope(workflow_id=run["id"],correlation_id="test",source_service="test",
        event_type="simulation.completed",actor="qa")
    assert client.post("/api/v1/platform/events/publish",json=event.model_dump(mode="json")).status_code==401
    first=client.post("/api/v1/platform/events/publish",headers=AUTH,json=event.model_dump(mode="json")).json()
    second=client.post("/api/v1/platform/events/publish",headers=AUTH,json=event.model_dump(mode="json")).json()
    assert first["delivered"] and second["duplicate"]

def test_a2a_is_typed_persisted_and_idempotent(client,db):
    run=ready_run(client); message=A2AMessage(workflow_id=run["id"],correlation_id="a2a-contract",sender="nexus-orchestrator",
        receiver="verification-agent",action="verify",expires_at=utcnow()+timedelta(minutes=5))
    for _ in range(2):
        assert client.post("/api/v1/platform/a2a/messages",headers=AUTH,json=message.model_dump(mode="json")).status_code==200
    assert db.query(A2AMessageRecord).filter_by(message_id=message.message_id).count()==1

def test_mcp_tools_are_authenticated_read_only_and_backend_driven(client):
    run=ready_run(client); tools=client.get("/api/v1/platform/mcp/tools").json()
    assert len(tools)==13 and not any(x["production_mutation"] for x in tools)
    payload={"workflow_id":run["id"],"correlation_id":"mcp-test","arguments":{}}
    assert client.post("/api/v1/platform/mcp/tools/get_tournament_results",json=payload).status_code==401
    result=client.post("/api/v1/platform/mcp/tools/get_tournament_results",headers=AUTH,json=payload).json()
    assert result["result"]["recommended_candidate_id"] and result["production_action"]=="NOT_EXECUTED"

def test_models_advisory_only_and_invocations_persisted(client,db):
    run=ready_run(client)
    reasoning=client.post("/api/v1/platform/reasoning/gemini",headers=AUTH,json={"workflow_id":run["id"],"evidence_ids":["e1"],"evidence":[{"id":"e1"}],"purpose":"contradictions"}).json()
    policy=client.post("/api/v1/platform/gemma/policy/review",headers=AUTH,json={"workflow_id":run["id"],"candidate":{"id":"fast"},"deterministic_gates":[{"gate":"failover","passed":False}],"evidence_ids":["e1"]}).json()
    assert not reasoning["authoritative"]
    assert not policy["gate_override"] and not policy["approval_authority"]
    assert db.query(IntegrationInvocation).count()>=2

def test_vertex_supplement_preserves_deterministic_authority(client):
    run=ready_run(client); result=client.get(f"/api/v1/platform/forecasts/{run['id']}/supplemental").json()
    assert result["authoritative_model"]=="bounded-linear-saturation"
    assert result["fallback_status"]=="DETERMINISTIC_BASELINE_USED"

def test_request_size_and_security_headers(client):
    response=client.get("/health")
    assert response.headers["x-content-type-options"]=="nosniff"
    oversized=client.post("/api/v1/platform/mcp/tools/get_evidence",headers={**AUTH,"Content-Length":"300000"},content=b"{}")
    assert oversized.status_code==413
