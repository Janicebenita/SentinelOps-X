from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated process configuration shared by API and service entry points.

    Defaults are intentionally suitable only for local deterministic execution.
    Managed environments must inject identity and secret values through their
    runtime configuration (Cloud Run uses Secret Manager references).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/sentinelops.db"
    llm_provider: str = "mock"
    demo_repo_path: Path = Path(".")
    demo_log_path: Path = Path("data/logs/demo.jsonl")
    demo_metrics_path: Path = Path("data/metrics/demo.jsonl")
    demo_traces_path: Path = Path("data/traces/demo.jsonl")
    sandbox_image: str = "sentinelops-sandbox:latest"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    demo_app_url: str = "http://127.0.0.1:8001"
    model_timeout_seconds: float = 30.0
    environment: str = "development"
    production_execution: bool = False
    intern_access_code: str = "0000"
    senior_access_code: str = "1111"
    role_token_secret: str = "development-only-replace-me"
    role_token_expiry_minutes: int = 10
    google_cloud_project: str = ""
    google_cloud_region: str = "asia-south1"
    google_genai_use_vertexai: bool = False
    google_api_key: str = ""
    vertex_model: str = "gemini-2.5-flash"
    bigquery_dataset: str = "sentinelops_nexus"
    pubsub_topic: str = "sentinelops-workflow-events"
    gemma_service_url: str = ""
    oidc_issuer: str = ""
    oidc_audience: str = ""
    integration_token: str = "development-integration-token"
    rate_limit_per_minute: int = 120
    max_request_bytes: int = 262144
    otel_exporter_otlp_endpoint: str = ""
    antigravity_endpoint: str = ""
    antigravity_participant_access: bool = False

    @model_validator(mode="after")
    def enforce_safety_invariants(self) -> "Settings":
        # SentinelOps records decisions but deliberately has no production
        # execution authority. Rejecting this at configuration load prevents a
        # deployment flag from silently weakening that architectural boundary.
        if self.production_execution:
            raise ValueError("PRODUCTION_EXECUTION must remain false")
        if self.role_token_expiry_minutes <= 0:
            raise ValueError("ROLE_TOKEN_EXPIRY_MINUTES must be positive")
        if self.rate_limit_per_minute <= 0 or self.max_request_bytes <= 0:
            raise ValueError("request safety limits must be positive")
        return self


settings = Settings()
