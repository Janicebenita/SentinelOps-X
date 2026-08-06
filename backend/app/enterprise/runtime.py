from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import time
from datetime import timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..llm.gemini_provider import GeminiProvider
from ..models import A2AMessageRecord, IntegrationInvocation, NexusRun
from .contracts import A2AMessage, EventEnvelope, EvidenceReasoningOutput, EvidenceReasoningRequest, PolicyReviewRequest, utcnow

def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False

STATUSES = {
    "Google AI Studio": "LOCAL_ADAPTER_ONLY",
    "Gemini": "IMPLEMENTED_REQUIRES_CREDENTIALS",
    "Gemma": "IMPLEMENTED_REQUIRES_CREDENTIALS" if settings.gemma_service_url else "LOCAL_ADAPTER_ONLY",
    "ADK": "LOCAL_ADAPTER_ONLY",
    "A2A": "IMPLEMENTED_AND_VERIFIED",
    "MCP": "IMPLEMENTED_AND_VERIFIED",
    "Vertex AI": "ROADMAP_ONLY",
    "BigQuery": "ROADMAP_ONLY",
    "Pub/Sub": "LOCAL_ADAPTER_ONLY",
    "Cloud Run": "IMPLEMENTED_REQUIRES_CREDENTIALS",
    "Antigravity": "DOCUMENTATION_UNAVAILABLE",
    "OpenTelemetry": "ROADMAP_ONLY",
    "OAuth2/JWT": "LOCAL_ADAPTER_ONLY",
    "Rate limiting": "IMPLEMENTED_AND_VERIFIED",
}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def trace_id() -> str:
    return uuid4().hex


class LocalEventBus:
    """Idempotent in-process adapter. Cloud deployments replace publish with Pub/Sub."""
    _delivered: set[str] = set()
    _dead_letters: list[dict[str, Any]] = []

    def publish(self, envelope: EventEnvelope) -> dict[str, Any]:
        if envelope.event_id in self._delivered:
            return {"delivered": False, "duplicate": True, "event_id": envelope.event_id}
        self._delivered.add(envelope.event_id)
        return {"delivered": True, "duplicate": False, "event_id": envelope.event_id, "trace_id": envelope.trace_id}

    def dead_letter(self, envelope: EventEnvelope, reason: str) -> None:
        self._dead_letters.append({"event": envelope.model_dump(mode="json"), "reason": reason})


event_bus = LocalEventBus()


def persist_a2a(db: Session, message: A2AMessage) -> A2AMessageRecord:
    existing = db.scalar(select(A2AMessageRecord).where(A2AMessageRecord.message_id == message.message_id))
    if existing:
        return existing
    row = A2AMessageRecord(message_id=message.message_id, workflow_id=message.workflow_id, task_id=message.task_id,
        correlation_id=message.correlation_id, sender=message.sender, receiver=message.receiver, action=message.action,
        status=message.status, payload_json=message.model_dump(mode="json"), trace_id=message.trace_id,
        retry_count=message.retry_count, expires_at=message.expires_at)
    db.add(row); db.commit(); db.refresh(row)
    return row


def invoke(db: Session, name: str, workflow_id: int | None, operation: str, inputs: Any, output: Any,
           *, fallback: bool, model: str | None = None, prompt: str | None = None, started: float | None = None) -> IntegrationInvocation:
    row = IntegrationInvocation(integration=name, workflow_id=workflow_id, status="fallback" if fallback else "success",
        model_name=model, prompt_version=prompt, input_references=[digest(inputs)], output_hash=digest(output),
        latency_ms=max(0, int((time.perf_counter() - (started or time.perf_counter())) * 1000)), token_usage={},
        trace_id=trace_id(), fallback_used=fallback)
    db.add(row); db.commit(); db.refresh(row)
    return row


def reason_with_gemini(db: Session, request: EvidenceReasoningRequest) -> dict[str, Any]:
    started = time.perf_counter()
    fallback_output = {"purpose": request.purpose, "summary": f"Reviewed {len(request.evidence)} persisted evidence artifacts.",
        "contradictions": [], "missing_evidence": [] if request.evidence else ["No evidence supplied"],
        "evidence_ids": request.evidence_ids, "authoritative": False, "production_action": "NOT_EXECUTED"}
    output = fallback_output; fallback = True
    if os.getenv("GEMINI_API_KEY"):
        try:
            task = ("Use only this supplied evidence. Never calculate authoritative forecasts, decide gates, approve, "
                "or mutate state. Return the required JSON schema.\n" + json.dumps(request.model_dump(mode="json"), sort_keys=True))
            output = GeminiProvider(timeout=settings.model_timeout_seconds).generate(task, EvidenceReasoningOutput).model_dump()
            fallback = False
        except ValueError:
            output = fallback_output
    call = invoke(db, "Gemini", request.workflow_id, request.purpose, request.model_dump(mode="json"), output,
        fallback=fallback, model=settings.vertex_model, prompt="evidence-reasoning-v1", started=started)
    return {**output, "fallback_used": fallback, "trace_id": call.trace_id, "output_hash": call.output_hash}


def review_with_gemma(db: Session, request: PolicyReviewRequest) -> dict[str, Any]:
    started = time.perf_counter()
    failed = [g.get("gate", "unknown") for g in request.deterministic_gates if not g.get("passed", False)]
    output = {"classification": "CONSISTENT" if not failed else "REQUIRES_REVIEW", "failed_gate_references": failed,
        "evidence_complete": bool(request.evidence_ids), "advisory_only": True, "gate_override": False,
        "approval_authority": False, "production_action": "NOT_EXECUTED"}
    fallback = True
    if settings.gemma_service_url:
        try:
            import httpx
            response = httpx.post(f"{settings.gemma_service_url.rstrip('/')}/v1/policy/review",
                json=request.model_dump(mode="json"), timeout=settings.model_timeout_seconds)
            response.raise_for_status()
            remote = response.json()
            if remote.get("gate_override") is not False or remote.get("approval_authority") is not False:
                raise ValueError("Gemma response attempted to exceed advisory authority")
            output = {**output, **remote, "gate_override": False, "approval_authority": False,
                "advisory_only": True, "production_action": "NOT_EXECUTED"}
            fallback = False
        except (httpx.HTTPError, ValueError, TypeError):
            fallback = True
    call = invoke(db, "Gemma", request.workflow_id, "policy_review", request.model_dump(mode="json"), output,
        fallback=fallback, model="gemma-policy-adapter", prompt="policy-review-v1", started=started)
    return {**output, "fallback_used": fallback, "trace_id": call.trace_id}


def supplemental_forecast(db: Session, run: NexusRun) -> dict[str, Any]:
    deterministic = run.forecast_json
    output = {"deterministic_forecast": deterministic, "vertex_supplemental_forecast": None,
        "variance_minutes": None, "fallback_status": "DETERMINISTIC_BASELINE_USED",
        "evidence_references": ["forecast_json"], "authoritative_model": "bounded-linear-saturation"}
    call = invoke(db, "Vertex AI", run.id, "supplemental_forecast", deterministic, output, fallback=True,
        model="vertex-supplemental-adapter")
    return {**output, "trace_id": call.trace_id}


def integration_health(db: Session) -> list[dict[str, Any]]:
    rows = []
    for name, configured_status in STATUSES.items():
        last = db.scalar(select(IntegrationInvocation).where(IntegrationInvocation.integration == name).order_by(IntegrationInvocation.id.desc()))
        verified = bool(last and last.status == "success" and not last.fallback_used)
        status = "IMPLEMENTED_AND_VERIFIED" if verified else configured_status
        rows.append({"integration": name, "status": status, "last_health_check": utcnow(),
            "configured_service": {"Gemini": settings.vertex_model, "Gemma": settings.gemma_service_url or "local-policy-adapter",
                "BigQuery": settings.bigquery_dataset, "Pub/Sub": settings.pubsub_topic}.get(name, name.lower().replace(" ", "-")),
            "last_successful_call": last.created_at if verified and last else None, "fallback_status": "ACTIVE" if last and last.fallback_used else "NOT_INVOKED",
            "trace_id": last.trace_id if last else None, "documentation": f"/docs#{name.lower().replace(' ', '-')}",
            "production_action": "NOT_EXECUTED"})
    return rows


def expiry(minutes: int = 10):
    return utcnow() + timedelta(minutes=minutes)
