from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from backend.app.database import Base,engine,get_db
from backend.app.config import settings
from backend.app.enterprise.contracts import PolicyReviewRequest
from backend.app.enterprise.runtime import review_with_gemma

@asynccontextmanager
async def lifespan(_:FastAPI): Base.metadata.create_all(engine); yield
app=FastAPI(title="sentinelops-gemma-service",version="1.0.0",lifespan=lifespan)
Db=Annotated[Session,Depends(get_db)]
@app.get("/health")
def health(): return {"status":"ok","service":"gemma-policy","production_action":"NOT_EXECUTED"}
@app.get("/readiness")
def readiness(): return {"ready":True,"provider":"remote" if settings.gemma_service_url else "local-fallback","production_action":"NOT_EXECUTED"}
@app.post("/v1/policy/review")
def policy_review(payload:PolicyReviewRequest,db:Db): return review_with_gemma(db,payload)
@app.post("/v1/evidence/check")
def evidence_check(payload:PolicyReviewRequest,db:Db): return review_with_gemma(db,payload)
