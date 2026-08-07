"""Adversarial release checks for authorization, configuration, and safety.

These tests intentionally exercise architectural boundaries rather than only
happy-path line coverage. They are kept separate so CI can identify a failed
enterprise assurance control without obscuring the functional suite.
"""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from pydantic import ValidationError

from backend.app.auth.roles import _b64, _secret, _unb64
from backend.app.config import Settings, settings
from backend.app.enterprise.router import TOOLS


FORBIDDEN_OPERATIONS = {
    "deploy",
    "scale",
    "rollback",
    "roll-back",
    "reconfigure",
    "shell",
    "execute-production",
    "production/execute",
    "infrastructure/mutate",
}


def _ready_run(client):
    run = client.post("/api/v1/demo/seed").json()
    return client.post(f"/api/v1/workflows/{run['id']}/run-all").json()


def _resign(token: str, **claims):
    """Modify claims and re-sign to test semantic validation after HMAC passes."""
    header, body, _ = token.split(".")
    payload = json.loads(_unb64(body))
    payload.update(claims)
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signing = f"{header}.{body}"
    signature = _b64(hmac.new(_secret(), signing.encode(), hashlib.sha256).digest())
    return f"{signing}.{signature}"


def test_deterministic_business_outputs_and_hashes_are_reproducible(client):
    first = _ready_run(client)
    second = _ready_run(client)

    assert first["forecast_json"]["predicted_crossing_minutes"] == 30
    assert first["forecast_json"]["predicted_customer_impact_minutes"] == 45
    assert len(first["scenarios_json"]) == 12
    assert first["tournament_json"]["recommended_candidate_id"] == "optimal"
    fast = next(c for c in first["tournament_json"]["candidates"] if c["candidate_id"] == "fast")
    optimal = next(c for c in first["tournament_json"]["candidates"] if c["candidate_id"] == "optimal")
    assert fast["eligible"] is False
    assert optimal["eligible"] is True
    assert first["twin_json"]["manifest_hash"] == second["twin_json"]["manifest_hash"]
    assert [s["result_hash"] for s in first["scenarios_json"]] == [s["result_hash"] for s in second["scenarios_json"]]


def test_signed_role_token_rejects_missing_role_bad_issuer_and_bad_audience(client, monkeypatch):
    run = _ready_run(client)
    monkeypatch.setattr(settings, "oidc_issuer", "https://issuer.example")
    monkeypatch.setattr(settings, "oidc_audience", "sentinelops-api")
    verified = client.post(
        "/api/v1/auth/verify-role",
        json={"actor_name": "Senior QA", "access_code": "1111"},
    ).json()
    payload = {
        "actor_name": "Senior QA",
        "decision": "approve",
        "rationale": "All deterministic gates and evidence were reviewed.",
    }

    for token in (
        _resign(verified["verification_token"], role=None),
        _resign(verified["verification_token"], iss="https://attacker.example"),
        _resign(verified["verification_token"], aud="different-api"),
        "not-valid-payload.not-valid-payload.not-valid-signature",
    ):
        response = client.post(
            f"/api/v1/workflows/{run['id']}/approve",
            json={**payload, "verification_token": token},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "INVALID_ROLE_TOKEN"


def test_decision_replay_is_rejected_by_authoritative_workflow_state(client):
    run = _ready_run(client)
    verified = client.post(
        "/api/v1/auth/verify-role",
        json={"actor_name": "Senior QA", "access_code": "1111"},
    ).json()
    decision = {
        "actor_name": "Senior QA",
        "decision": "approve",
        "rationale": "All deterministic gates and evidence were reviewed.",
        "verification_token": verified["verification_token"],
    }
    assert client.post(f"/api/v1/workflows/{run['id']}/approve", json=decision).status_code == 200
    replay = client.post(f"/api/v1/workflows/{run['id']}/approve", json=decision)
    assert replay.status_code == 409
    assert "awaiting human" in replay.json()["detail"].lower()


def test_no_route_or_mcp_tool_can_mutate_production_infrastructure(client):
    paths = {path.lower() for path in client.get("/openapi.json").json()["paths"]}
    assert not {
        path for path in paths if any(operation in path for operation in FORBIDDEN_OPERATIONS)
    }
    assert not {
        tool for tool in TOOLS if any(operation in tool.lower() for operation in FORBIDDEN_OPERATIONS)
    }


def test_configuration_fails_closed_for_production_execution_and_unsafe_secrets():
    with pytest.raises(ValidationError, match="PRODUCTION_EXECUTION"):
        Settings(_env_file=None, production_execution=True)
    with pytest.raises(ValidationError, match="request safety limits"):
        Settings(_env_file=None, rate_limit_per_minute=0)
    production = Settings(
        _env_file=None,
        environment="production",
        role_token_secret="managed-secret-reference-value",
        integration_token="managed-integration-reference-value",
    )
    assert production.production_execution is False
