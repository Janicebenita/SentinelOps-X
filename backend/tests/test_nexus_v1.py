from __future__ import annotations

import hashlib
import io
import zipfile

from sqlalchemy import select

from backend.app.models import NexusAuditEvent
from backend.app.schemas.nexus_contracts import RunCreate, TwinControls
from backend.app.services import nexus_workflow as nexus


def test_seeded_forecast_and_controls_are_deterministic(db):
    run = nexus.create_run(db, RunCreate(name="Payment Service capacity forecast"))
    nexus.observe(db, run)
    first = nexus.predict(db, run)
    assert first.predicted_crossing_minutes == 30
    assert first.predicted_customer_impact_minutes == 45

    default = nexus.telemetry(TwinControls())
    repeated = nexus.telemetry(TwinControls())
    constrained = nexus.telemetry(TwinControls(redis_capacity=9000))
    replicated = nexus.telemetry(TwinControls(application_replicas=8))
    assert default == repeated
    assert constrained[1].redis_memory_pct > default[1].redis_memory_pct
    assert replicated[3].queue_depth < default[3].queue_depth


def test_full_workflow_is_reproducible_and_human_gated(db):
    run = nexus.create_run(db, RunCreate(name="Payment Service capacity forecast"))
    nexus.run_all(db, run)
    assert run.state == "RECOMMENDED"
    assert len(run.scenarios_json) == 12
    assert run.tournament_json["recommended_candidate_id"] in {"safe", "optimal"}
    fast = next(item for item in run.tournament_json["candidates"] if item["candidate_id"] == "fast")
    assert fast["eligible"] is False
    assert any(gate["gate"] == "failover_test" and not gate["passed"] for gate in fast["gates"])
    assert run.production_action_executed is False

    manifest = run.twin_json["manifest_hash"]
    scenario_hashes = [item["result_hash"] for item in run.scenarios_json]
    nexus.reset(db)
    replay = nexus.create_run(db, RunCreate(name="Payment Service capacity forecast"))
    nexus.run_all(db, replay)
    assert replay.twin_json["manifest_hash"] == manifest
    assert [item["result_hash"] for item in replay.scenarios_json] == scenario_hashes


def test_scenarios_are_calculated_from_explore_controls(db):
    baseline = nexus.create_run(db, RunCreate(name="Baseline"))
    nexus.run_all(db, baseline)
    resilient = nexus.create_run(db, RunCreate(
        name="Resilient",
        controls=TwinControls(redis_capacity=50000, application_replicas=12, dependency_latency_ms=10),
    ))
    nexus.run_all(db, resilient)

    base_growth = next(x for x in baseline.scenarios_json if x["scenario_id"] == "baseline-growth")
    resilient_growth = next(x for x in resilient.scenarios_json if x["scenario_id"] == "baseline-growth")
    assert resilient_growth["p95_ms"] < base_growth["p95_ms"]
    assert resilient_growth["error_rate_pct"] < base_growth["error_rate_pct"]
    assert resilient_growth["result_hash"] != base_growth["result_hash"]
    assert resilient_growth["inputs"]["base_controls"]["redis_capacity"] == 50000


def test_invalid_transition_and_approval_bypass_are_blocked(db):
    run = nexus.create_run(db, RunCreate(name="Payment Service capacity forecast"))
    try:
        nexus.predict(db, run)
    except ValueError as exc:
        assert "CREATED" in str(exc)
    else:
        raise AssertionError("Prediction bypassed the state policy")

    response = nexus.HumanDecisionInput(actor="judge", decision="approve", rationale="Evidence reviewed")
    try:
        nexus.decide(db, run, response)
    except ValueError as exc:
        assert "RECOMMENDED" in str(exc)
    else:
        raise AssertionError("Approval bypassed the state policy")


def test_audit_chain_and_export_hashes(db):
    run = nexus.create_run(db, RunCreate(name="Payment Service capacity forecast"))
    nexus.run_all(db, run)
    decision = nexus.HumanDecisionInput(actor="judge", decision="approve", rationale="All mandatory gates passed")
    nexus.decide(db, run, decision)
    assert nexus.verify_audit(db, run.id)["valid"] is True

    bundle = nexus.export_zip(db, run)
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        names = set(archive.namelist())
        assert {"incident.json", "twin-manifest.json", "evidence.json", "forecast.json", "scenarios.json", "tournament.json", "verification.json", "business-impact.json", "executive-brief.md", "audit.json", "manifest.sha256"} <= names
        for line in archive.read("manifest.sha256").decode().splitlines():
            expected, name = line.split("  ", 1)
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected

    event = db.scalar(select(NexusAuditEvent).where(NexusAuditEvent.run_id == run.id).order_by(NexusAuditEvent.sequence))
    assert event is not None
    event.payload_json = {"tampered": True}
    db.commit()
    assert nexus.verify_audit(db, run.id)["valid"] is False


def test_versioned_api_end_to_end(client):
    assert client.get("/api/v1/health").json()["production_action"] == "NOT EXECUTED"
    seeded = client.post("/api/v1/demo/seed").json()
    run_id = seeded["id"]
    completed = client.post(f"/api/v1/workflows/{run_id}/run-all")
    assert completed.status_code == 200
    assert completed.json()["state"] == "RECOMMENDED"
    assert len(client.get(f"/api/v1/workflows/{run_id}/evidence").json()) == 4
    assert len(client.get(f"/api/v1/workflows/{run_id}/timeline").json()) >= 9
    assert len(client.get(f"/api/v1/workflows/{run_id}/agents").json()) >= 9

    uploaded = client.post(f"/api/v1/workflows/{run_id}/evidence/upload", json={
        "filename": "capacity.json",
        "category": "configuration",
        "content": '{"controls":{"redis_capacity":24000}}',
    })
    assert uploaded.status_code == 200
    assert uploaded.json()["source"] == "manual-upload/capacity.json"
    assert client.get(f"/api/v1/workflows/{run_id}/timeline").json()[-1]["event_type"] == "evidence.uploaded"

    wrong = client.post(f"/api/v1/workflows/{run_id}/approve", json={"actor": "judge", "decision": "reject", "rationale": "No"})
    assert wrong.status_code == 422
    approved = client.post(f"/api/v1/workflows/{run_id}/approve", json={"actor": "judge", "decision": "approve", "rationale": "Evidence reviewed"})
    assert approved.status_code == 200
    assert approved.json()["production_action"] == "NOT EXECUTED"
    exported = client.get(f"/api/v1/workflows/{run_id}/export")
    assert exported.status_code == 200
    assert exported.headers["content-type"] == "application/zip"
    assert client.get("/api/v1/audit/verify", params={"run_id": run_id}).json()["valid"] is True
