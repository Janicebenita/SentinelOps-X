from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
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
    google_cloud_region: str = "us-central1"
    google_genai_use_vertexai: bool = False
    google_api_key: str = ""
    vertex_model: str = "gemini-2.5-flash"
    bigquery_dataset: str = "sentinelops"
    pubsub_topic: str = "sentinelops-events"
    gemma_service_url: str = ""
    oidc_issuer: str = ""
    oidc_audience: str = ""
    integration_token: str = "development-integration-token"
    rate_limit_per_minute: int = 120
    max_request_bytes: int = 262144
    otel_exporter_otlp_endpoint: str = ""
settings = Settings()
