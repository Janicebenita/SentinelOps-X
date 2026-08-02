"""Exercise the seeded incident and assert every deterministic safety gate."""

from __future__ import annotations

import hashlib
from pathlib import Path

import httpx

from backend.app.config import settings
from backend.app.tools.patch_tools import PatchPolicyError, inspect_patch
from backend.app.tools.sandbox import validate_command

API = "http://localhost:8000/api"
BUG = {"items": [{"product_id": 1, "quantity": 2}], "discount_code": "SAVE10", "region": "TN"}

def source_hash() -> str:
    return hashlib.sha256(Path("demo_app/app/main.py").read_bytes()).hexdigest()

def main() -> int:
    assert settings.llm_provider == "mock"
    try: validate_command(["pytest", "-q; touch /tmp/escaped"])
    except ValueError: pass
    else: raise AssertionError("sandbox command validation allowed shell metacharacters")
    with httpx.Client(timeout=180) as client:
        client.post(f"{API}/demo/reset").raise_for_status()
        seed = client.post(f"{API}/demo/seed"); seed.raise_for_status(); incident_id = seed.json()["ids"][0]
        failure = client.post("http://localhost:8001/checkout", json=BUG)
        assert failure.status_code == 500
        client.post(f"{API}/incidents/{incident_id}/start").raise_for_status()
        client.post(f"{API}/incidents/{incident_id}/collect-evidence").raise_for_status()
        client.post(f"{API}/incidents/{incident_id}/generate-hypotheses").raise_for_status()
        hypotheses = client.get(f"{API}/incidents/{incident_id}/hypotheses").json()
        assert hypotheses[0]["title"] == "Nullable TN tax rate in discounted checkout"
        reproduction = client.post(f"{API}/incidents/{incident_id}/reproduce"); reproduction.raise_for_status()
        assert reproduction.json()["result"] == "confirmed"
        assert reproduction.json()["exit_code"] == 1
        client.post(f"{API}/incidents/{incident_id}/generate-patch").raise_for_status()
        before = source_hash()
        verification = client.post(f"{API}/incidents/{incident_id}/verify"); verification.raise_for_status()
        assert source_hash() == before
        failed = [check for check in verification.json() if not check["passed"]]
        assert not failed, [(check["test_type"], check["stdout"][-1500:], check["stderr"][-500:]) for check in failed]
        regression = next(check for check in verification.json() if check["test_type"] == "regression")
        assert regression["passed"] and regression["exit_code"] == 0
        assert client.post(f"{API}/incidents/{incident_id}/create-pr").status_code == 409
        evidence = client.get(f"{API}/incidents/{incident_id}/evidence").json()
        assert {item["evidence_type"] for item in evidence} >= {"log", "metric", "trace", "git"}
        audit = client.get(f"{API}/incidents/{incident_id}/audit-log").json()
        transitions = [event["output_json"]["to"] for event in audit if event["event_type"] == "state_transition"]
        assert transitions == [
            "ALERT_RECEIVED", "COLLECTING_EVIDENCE", "EVIDENCE_READY",
            "GENERATING_HYPOTHESES", "HYPOTHESES_READY", "REPRODUCING",
            "REPRODUCTION_CONFIRMED", "GENERATING_PATCH", "PATCH_READY",
            "VERIFYING", "VERIFICATION_PASSED", "AWAITING_APPROVAL",
        ]
        try: inspect_patch("+unsafe", ["sandbox/Dockerfile"], True)
        except PatchPolicyError: pass
        else: raise AssertionError("protected path policy did not reject patch")
        client.post(f"{API}/incidents/{incident_id}/approve", json={"approved_by": "e2e-operator"}).raise_for_status()
        client.post(f"{API}/incidents/{incident_id}/create-pr").raise_for_status()
        final_audit = client.get(f"{API}/incidents/{incident_id}/audit-log").json()
        final_transitions = [
            event["output_json"]["to"]
            for event in final_audit
            if event["event_type"] == "state_transition"
        ]
        assert final_transitions[-3:] == ["APPROVED", "PR_CREATED", "COMPLETED"]
        reset = client.post(f"{API}/demo/reset"); reset.raise_for_status()
        assert reset.json()["reset"] is True
        assert client.get(f"{API}/incidents").json() == []
    print("Seeded incident passed every evidence, sandbox, policy, approval, and audit assertion")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
