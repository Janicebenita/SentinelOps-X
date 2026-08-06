from fastapi.testclient import TestClient

from backend.app.main import app


def test_antigravity_status_is_truthful_and_read_only() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/integrations/antigravity/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "DOCUMENTATION_OR_ACCESS_BLOCKED"
    assert payload["configured"] is False
    assert payload["fallback_state"] == "DETERMINISTIC_LOCAL_SIMULATION"
    assert payload["official_runtime_invoked"] is False
    assert payload["production_action"] == "NOT_EXECUTED"
    assert "access_code" not in response.text.lower()
