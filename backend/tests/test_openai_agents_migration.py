from __future__ import annotations

import pytest
from sqlalchemy import select

pytest.importorskip("agents", reason="install the migration extra to test the SDK adapter")

from agents.exceptions import UserError  # noqa: E402

from backend.app.migrations.openai_agents_reliability import (  # noqa: E402
    MIGRATION_RUNTIME,
    analyze_reliability_tool,
    run_migrated_reliability_analysis,
)
from backend.app.models import NexusRun  # noqa: E402
from backend.app.schemas.nexus_contracts import (  # noqa: E402
    ReliabilityWorkerRequest,
    TwinControls,
)


def _request(correlation_id: str = "migration-test-001") -> ReliabilityWorkerRequest:
    return ReliabilityWorkerRequest(
        correlation_id=correlation_id,
        requested_by="migration-evaluator",
        name="SDK-migrated reliability analysis",
        controls=TwinControls(
            traffic_multiplier=2,
            redis_capacity=12000,
            application_replicas=4,
            dependency_latency_ms=50,
            source_label="evaluation/openai-agents-sdk",
        ),
    )


def test_sdk_migration_runs_real_strict_tool_and_preserves_safety_boundary(db):
    result = run_migrated_reliability_analysis(db, _request())

    assert result.runtime == MIGRATION_RUNTIME
    assert result.model_requests == 1
    assert result.generated_items == 2
    assert result.tool_name == "analyze_reliability"
    assert result.analysis.workflow_state == "AWAITING_HUMAN"
    assert result.analysis.approval.required is True
    assert result.analysis.approval.production_action == "NOT EXECUTED"
    assert result.analysis.recommendation.production_action == "NOT EXECUTED"
    assert result.analysis.audit_valid is True
    assert all(check.passed for check in result.analysis.safety_checks)

    run = db.get(NexusRun, result.analysis.workflow_id)
    assert run is not None
    assert run.production_action_executed is False


def test_sdk_migration_matches_native_result_for_same_contract(db):
    from backend.app.services.nexus_workflow import analyze_reliability_worker

    request = _request("migration-equivalence-001")
    native = analyze_reliability_worker(db, request)
    migrated = run_migrated_reliability_analysis(db, request).analysis

    assert migrated.result_hash == native.result_hash
    assert migrated.forecast == native.forecast
    assert migrated.tournament == native.tournament
    assert migrated.business_impact == native.business_impact
    assert migrated.recommendation == native.recommendation
    assert migrated.workflow_id != native.workflow_id


def test_sdk_tool_schema_reuses_the_versioned_worker_contract():
    schema = analyze_reliability_tool.params_json_schema

    assert analyze_reliability_tool.strict_json_schema is True
    assert schema["additionalProperties"] is False
    assert schema["properties"]["request"]["$ref"].endswith("/ReliabilityWorkerRequest")


def test_sdk_migration_does_not_hide_authoritative_failures(db, monkeypatch):
    from backend.app.migrations import openai_agents_reliability as migration

    def fail_worker(*_args, **_kwargs):
        raise ValueError("authoritative worker rejected the request")

    monkeypatch.setattr(migration, "analyze_reliability_worker", fail_worker)

    with pytest.raises(UserError, match="authoritative worker rejected") as error:
        migration.run_migrated_reliability_analysis(db, _request("migration-failure-001"))

    assert isinstance(error.value.__cause__, ValueError)
    assert db.scalar(select(NexusRun)) is None
