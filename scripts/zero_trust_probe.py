"""Reproducible in-memory release probe. It never touches production infrastructure."""
from __future__ import annotations

import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import A2AMessageRecord, IntegrationInvocation


def main() -> None:
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    Base.metadata.create_all(engine); db=sessionmaker(bind=engine,expire_on_commit=False)()
    app.dependency_overrides[get_db]=lambda:db
    with TestClient(app) as client:
        run=client.post("/api/v1/demo/seed").json(); run=client.post(f"/api/v1/workflows/{run['id']}/run-all").json()
        agent=client.post(f"/api/v1/workflows/{run['id']}/agents/prediction-agent/run",json={"actor_name":"zero-trust-probe"})
        auth={"Authorization":"Bearer development-integration-token"}
        reasoning=client.post("/api/v1/platform/reasoning/gemini",headers=auth,json={"workflow_id":run["id"],"evidence_ids":["ev-telemetry"],"evidence":[{"id":"ev-telemetry"}],"purpose":"correlate"}).json()
        messages=db.scalars(select(A2AMessageRecord).where(A2AMessageRecord.workflow_id==run["id"])).all()
        calls=db.scalars(select(IntegrationInvocation).where(IntegrationInvocation.workflow_id==run["id"])).all()
        audit=client.get(f"/api/v1/audit/verify?run_id={run['id']}").json()
        print(json.dumps({"workflow_id":run["id"],"agent_status":agent.status_code,"a2a_messages":len(messages),
            "a2a_trace_ids":sorted({x.trace_id for x in messages}),"model_trace_ids":[x.trace_id for x in calls],
            "gemini_fallback":reasoning["fallback_used"],"audit_valid":audit["valid"],
            "production_action":"NOT_EXECUTED"},indent=2))
    app.dependency_overrides.clear(); db.close()


if __name__=="__main__": main()
