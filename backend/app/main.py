from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from .api import nexus_router, router
from .enterprise import router as enterprise_router
from .config import settings
from .database import Base,SessionLocal,engine
from .models import Incident
from . import llm
from .tools.sandbox import get_sandbox
from .security import reset_rate_limits, security_middleware
from .integrations.antigravity import AntigravityStatus, get_antigravity_status
@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment.lower() not in {"development", "test"} and settings.integration_token == "development-integration-token":
        raise RuntimeError("INTEGRATION_TOKEN must be configured outside development")
    reset_rate_limits()
    Base.metadata.create_all(engine)
    yield

app=FastAPI(title="SentinelOps Nexus API",version="3.0.0",description="The Enterprise Operational Digital Twin: predictive, evidence-driven, and human-controlled",lifespan=lifespan)
app.middleware("http")(security_middleware)
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],allow_methods=["GET","POST"],allow_headers=["Content-Type"])
app.include_router(router)
app.include_router(nexus_router)
app.include_router(enterprise_router)
@app.get("/api/v1/integrations/antigravity/status", response_model=AntigravityStatus, tags=["Integrations"])
def antigravity_status() -> AntigravityStatus:
    return get_antigravity_status()
@app.get("/health")
def health():
    return {"status":"ok","backend":True,"provider":settings.llm_provider,"production_action":"NOT_EXECUTED"}

@app.get("/readiness")
def readiness():
    database=False; seeded=False
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1")); database=True; seeded=db.scalar(select(Incident.id).limit(1)) is not None
    except Exception: pass
    demo_app=True
    if settings.demo_app_url:
        try: demo_app=httpx.get(f"{settings.demo_app_url}/health",timeout=1).is_success
        except httpx.HTTPError: demo_app=False
    mode=get_sandbox(settings.sandbox_image).mode; actual=type(llm.get_provider(settings.llm_provider)).__name__.replace("LLMProvider","").replace("Provider","").lower()
    ready=database and demo_app and seeded and actual=="mock" and mode in {"docker","local"}
    return {"status":"ok" if ready else "degraded","ready":ready,"backend":True,"demo_app":demo_app,"database":database,"provider":actual,"configured_provider":settings.llm_provider,"provider_warning":llm.provider_warning,"mock_provider":actual=="mock","seeded":seeded,"sandbox_mode":mode,"auto_deploy":False}
