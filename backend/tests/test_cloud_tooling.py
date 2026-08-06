from pathlib import Path

import yaml  # type: ignore[import-untyped]

from backend.app.config import Settings
from scripts.provision_pubsub import TOPICS

ROOT = Path(__file__).parents[2]


def test_google_cloud_defaults_match_approved_target(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_REGION", raising=False)
    monkeypatch.delenv("BIGQUERY_DATASET", raising=False)
    monkeypatch.delenv("PUBSUB_TOPIC", raising=False)
    settings = Settings(_env_file=None)
    assert settings.google_cloud_region == "asia-south1"
    assert settings.bigquery_dataset == "sentinelops_nexus"
    assert settings.pubsub_topic == "sentinelops-workflow-events"


def test_bigquery_schema_contains_all_required_tables():
    ddl_files = sorted((ROOT / "sql" / "bigquery").glob("*.sql"))
    sql = "\n".join(path.read_text(encoding="utf-8") for path in ddl_files)
    tables = {
        "telemetry_events",
        "workflow_events",
        "agent_executions",
        "model_invocations",
        "scenario_results",
        "verification_results",
        "business_impact_estimates",
        "audit_event_exports",
        "forecast_evaluations",
    }
    assert all(f"`${{PROJECT}}.${{DATASET}}.{name}`" in sql for name in tables)
    assert len(ddl_files) == 9
    assert sql.count("PARTITION BY") == 9
    assert sql.count("CLUSTER BY") == 9
    audit = (ROOT / "sql" / "bigquery" / "audit_event_exports.sql").read_text(encoding="utf-8")
    for field in ("actor_type", "actor_id", "payload_json", "chain_position", "signature", "signer_key_id", "evidence_ids", "schema_version", "ingestion_timestamp"):
        assert field in audit


def test_pubsub_topics_match_required_contract():
    assert set(TOPICS) == {
        "sentinelops-agent-tasks",
        "sentinelops-scenario-events",
        "sentinelops-verification-events",
        "sentinelops-model-events",
        "sentinelops-evidence-events",
        "sentinelops-bigquery-events",
        "sentinelops-workflow-events",
    }


def test_cloud_build_and_run_cover_nine_services():
    build = yaml.safe_load((ROOT / "cloudbuild.yaml").read_text(encoding="utf-8"))
    assert build["substitutions"]["_REGION"] == "asia-south1"
    assert len(build["images"]) == 9
    manifests = list(
        yaml.safe_load_all((ROOT / "deploy" / "cloud-run" / "services.yaml").read_text(encoding="utf-8"))
    )
    assert {item["metadata"]["name"] for item in manifests} == {
        "sentinelops-frontend",
        "sentinelops-api-gateway",
        "sentinelops-orchestrator",
        "sentinelops-forecast-service",
        "sentinelops-simulation-service",
        "sentinelops-verification-service",
        "sentinelops-evidence-service",
        "sentinelops-gemma-service",
        "sentinelops-mcp-server",
    }


def test_cloud_workflow_uses_oidc_and_no_service_account_key():
    workflow = (ROOT / ".github" / "workflows" / "google-cloud-runtime.yml").read_text(
        encoding="utf-8"
    )
    assert "id-token: write" in workflow
    assert "workload_identity_provider" in workflow
    assert "workflow_dispatch" in workflow
    assert "service-account.json" not in workflow
    assert "GOOGLE_API_KEY" not in workflow


def test_frontend_cloud_run_uses_runtime_api_url_and_cors_update():
    dockerfile = (ROOT / "Dockerfile.frontend").read_text(encoding="utf-8")
    client = (ROOT / "frontend" / "src" / "api" / "client.ts").read_text(encoding="utf-8")
    deploy = (ROOT / "scripts" / "deploy_cloud_run.sh").read_text(encoding="utf-8")
    assert "runtime-config.js" in dockerfile and "API_BASE_URL" in dockerfile
    assert "__SENTINELOPS_CONFIG__" in client
    assert "API_BASE_URL=${API_URL}" in deploy
    assert "CORS_ORIGINS=${FRONTEND_URL}" in deploy
