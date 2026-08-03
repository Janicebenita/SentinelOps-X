import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from .api import nexus_router, router
from .config import settings
from .database import Base,SessionLocal,engine
from .models import Incident
from . import llm
from .tools.sandbox import get_sandbox
from .services.demo_seed import ensure_seeded
Base.metadata.create_all(engine)
with SessionLocal() as startup_db:
    ensure_seeded(startup_db)
app=FastAPI(title="SentinelOps Nexus API",version="2.0.0",description="The Enterprise Operational Digital Twin: predictive, evidence-driven, and human-controlled")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],allow_methods=["GET","POST"],allow_headers=["Content-Type"])
app.include_router(router)
app.include_router(nexus_router)
@app.get("/health")
def health():
    database=False; seeded=False
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1")); database=True; seeded=db.scalar(select(Incident.id).limit(1)) is not None
    except Exception: pass
    try: demo_app=httpx.get(f"{settings.demo_app_url}/health",timeout=1).is_success
    except httpx.HTTPError: demo_app=False
    mode=get_sandbox(settings.sandbox_image).mode; actual=type(llm.get_provider(settings.llm_provider)).__name__.replace("LLMProvider","").replace("Provider","").lower()
    ready=database and demo_app and seeded and actual=="mock" and mode in {"docker","local"}
    return {"status":"ok" if ready else "degraded","ready":ready,"backend":True,"demo_app":demo_app,"database":database,"provider":actual,"configured_provider":settings.llm_provider,"provider_warning":llm.provider_warning,"mock_provider":actual=="mock","seeded":seeded,"sandbox_mode":mode,"auto_deploy":False}
