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
settings = Settings()
