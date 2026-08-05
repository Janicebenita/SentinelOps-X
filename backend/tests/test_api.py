def test_seed_and_approval_gate(client):
    assert client.post("/api/demo/seed").status_code == 200
    incident = client.get("/api/incidents").json()[-1]
    assert client.post(f"/api/incidents/{incident['id']}/create-pr").status_code == 409

def test_provider_health_is_safe(client):
    response=client.get("/health")
    assert response.status_code==200
    body=response.json()
    assert body["provider"]=="mock" and "api_key" not in str(body).lower()
    assert body["production_action"]=="NOT_EXECUTED"

def test_full_mock_workflow(client, monkeypatch):
    from backend.app.agent import workflow
    from backend.app.tools.sandbox import CommandResult
    calls = {"count": 0}
    def sandbox_result(command, workspace, image):
        calls["count"] += 1
        exit_code = 1 if calls["count"] == 1 else 0
        return CommandResult("sandbox evidence", "", exit_code, 0.01)
    class StubSandbox:
        mode = "docker"
        def run(self, command, workspace, timeout=90):
            return sandbox_result(command, workspace, "test-image")
    monkeypatch.setattr(workflow, "get_sandbox", lambda image: StubSandbox())
    client.post("/api/demo/seed")
    iid = client.get("/api/incidents").json()[-1]["id"]
    for action in ["start", "collect-evidence", "generate-hypotheses", "reproduce", "generate-patch", "verify"]:
        response = client.post(f"/api/incidents/{iid}/{action}")
        assert response.status_code == 200, response.text
    hypotheses = client.get(f"/api/incidents/{iid}/hypotheses").json()
    assert len(hypotheses) >= 2 and hypotheses[0]["confidence"] > 0.9
    checks = client.get(f"/api/incidents/{iid}/verification").json()
    assert len(checks) == 6 and all(x["passed"] for x in checks)
    assert client.get(f"/api/incidents/{iid}").json()["current_state"] == "AWAITING_APPROVAL"
    assert client.post(f"/api/incidents/{iid}/approve", json={"approved_by": "operator"}).status_code == 200
    assert client.post(f"/api/incidents/{iid}/create-pr").json()["status"] == "draft"
    assert len(client.get(f"/api/incidents/{iid}/audit-log").json()) >= 10

def test_finale_endpoints_require_no_deployment_path(client):
    client.post("/api/demo/seed")
    iid=client.get("/api/incidents").json()[-1]["id"]
    assert client.post(f"/api/incidents/{iid}/digital-twin").status_code==200
    replay=client.post(f"/api/incidents/{iid}/replay",json={"attempts":3}).json()
    assert len(replay)==3 and len({x["deterministic_hash"] for x in replay})==1
    tournament=client.post(f"/api/incidents/{iid}/repair-tournament").json()
    assert tournament["recommended_candidate"]["candidate_id"]=="candidate-c"
    assert client.post(f"/api/incidents/{iid}/deploy").status_code==404
