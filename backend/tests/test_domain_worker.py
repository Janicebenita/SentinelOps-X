from __future__ import annotations

from sqlalchemy import select

from backend.app.models import NexusAuditEvent, NexusRun
from backend.app.schemas.nexus_contracts import ReliabilityWorkerRequest, TwinControls
from backend.app.services import nexus_workflow as workflow


def test_domain_worker_returns_portable_human_gated_contract(db):
    request = ReliabilityWorkerRequest(
        correlation_id="campaign-baseline-001",
        requested_by="campaign-reviewer",
        controls=TwinControls(
            traffic_multiplier=1.5,
            redis_capacity=12000,
            application_replicas=4,
            dependency_latency_ms=35,
        ),
    )

    first = workflow.analyze_reliability_worker(db, request)
    second = workflow.analyze_reliability_worker(db, request)

    assert first.contract_version == "sentinelops.reliability-analysis.v1"
    assert first.workflow_state == "AWAITING_HUMAN"
    assert first.operating_mode == "deterministic"
    assert first.approval.required is True
    assert first.approval.production_action == "NOT EXECUTED"
    assert first.recommendation.production_action == "NOT EXECUTED"
    assert first.audit_valid is True
    assert first.result_hash == second.result_hash
    assert first.workflow_id != second.workflow_id
    assert len(first.evidence) == 4
    assert len(first.tournament.candidates) == 3
    assert all(check.passed for check in first.safety_checks)
    assert any(check.name == "human_approval_required" for check in first.safety_checks)

    run = db.get(NexusRun, first.workflow_id)
    assert run is not None
    assert run.production_action_executed is False
    events = list(
        db.scalars(
            select(NexusAuditEvent)
            .where(NexusAuditEvent.run_id == first.workflow_id)
            .order_by(NexusAuditEvent.sequence)
        )
    )
    assert events[-1].event_type == "domain_worker.completed"
    assert events[-1].payload_json["result_hash"] == first.result_hash
    assert workflow.verify_audit(db, first.workflow_id)["valid"] is True


def test_domain_worker_api_rejects_unknown_fields_and_exposes_schema(client):
    invalid = client.post(
        "/api/v1/domain-workers/reliability-analysis",
        json={
            "contract_version": "sentinelops.reliability-analysis.v1",
            "correlation_id": "campaign-invalid-001",
            "unexpected": "not accepted",
        },
    )
    assert invalid.status_code == 422

    response = client.post(
        "/api/v1/domain-workers/reliability-analysis",
        json={
            "contract_version": "sentinelops.reliability-analysis.v1",
            "correlation_id": "campaign-api-001",
            "requested_by": "competition-reviewer",
            "name": "Checkout reliability analysis",
            "controls": {
                "traffic_multiplier": 2,
                "redis_capacity": 12000,
                "application_replicas": 4,
                "dependency_latency_ms": 50,
                "failover_state": "primary",
                "seed": 20260808,
                "source_label": "demo/checkout-service",
                "normalization_notes": [],
                "telemetry_points": [],
                "business": {
                    "conversion_rate": 0.034,
                    "average_order_value_inr": 3200,
                    "risk_window_minutes": 60,
                    "projected_failure_rate": 0.18,
                    "sla_penalty_inr": 250000,
                },
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "sentinelops.reliability-analysis.v1"
    assert body["correlation_id"] == "campaign-api-001"
    assert body["workflow_state"] == "AWAITING_HUMAN"
    assert body["approval"]["required"] is True
    assert body["approval"]["authorized_roles"] == ["SENIOR_DEVELOPER"]
    assert body["approval"]["production_action"] == "NOT EXECUTED"
    assert body["audit_valid"] is True
    assert len(body["result_hash"]) == 64

    openapi = client.get("/openapi.json").json()
    operation = openapi["paths"]["/api/v1/domain-workers/reliability-analysis"]["post"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]


def test_domain_worker_records_bounded_failure_without_production_action(
    client, db, monkeypatch, caplog
):
    def fail_simulation(*_args, **_kwargs):
        raise RuntimeError("simulated isolated stage failure")

    monkeypatch.setattr(workflow, "simulate", fail_simulation)
    response = client.post(
        "/api/v1/domain-workers/reliability-analysis",
        json={
            "correlation_id": "campaign-failure-001",
            "name": "Failure isolation example",
        },
    )

    assert response.status_code == 409
    run = db.scalar(select(NexusRun).order_by(NexusRun.id.desc()))
    assert run is not None
    assert run.state == "TWIN_READY"
    assert run.production_action_executed is False
    events = list(
        db.scalars(
            select(NexusAuditEvent)
            .where(NexusAuditEvent.run_id == run.id)
            .order_by(NexusAuditEvent.sequence)
        )
    )
    assert events[-1].event_type == "domain_worker.failed"
    assert events[-1].payload_json["error_type"] == "RuntimeError"
    assert "simulated isolated stage failure" not in str(events[-1].payload_json)
    assert "simulated isolated stage failure" not in caplog.text
    assert workflow.verify_audit(db, run.id)["valid"] is True
