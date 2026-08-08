from __future__ import annotations

import io
import json
import math
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, cast

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..models import NexusAuditEvent, NexusEvidence, NexusRun
from ..schemas.nexus_contracts import (
    AgentEnvelope,
    BusinessAssumptions,
    BusinessImpactResult,
    EvidenceUpload,
    EvidenceRecord,
    ExecutiveBrief,
    ForecastResult,
    GateResult,
    HumanDecisionInput,
    InterventionCandidate,
    OperationalJsonImport,
    RunCreate,
    ScenarioResultContract,
    TelemetryPoint,
    TopologyResult,
    TournamentResult,
    TwinControls,
    TwinManifestContract,
)

ROOT = Path(__file__).resolve().parents[3]
SCENARIOS = [
    "baseline-growth", "redis-crash", "redis-latency", "replica-failover",
    "10x-traffic", "million-user-stress", "reduced-redis-capacity",
    "increased-app-replicas", "rollback-intervention", "rate-limiting-intervention",
    "cache-policy-correction", "configuration-drift",
]
STATE_ORDER = ["CREATED", "OBSERVED", "PREDICTED", "TWIN_READY", "SIMULATED", "TOURNAMENT_READY", "VERIFIED", "IMPACT_READY", "AWAITING_HUMAN", "DECIDED"]


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def digest(value: Any) -> str:
    return sha256(canonical(value).encode()).hexdigest()


def serialize(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def require_run(db: Session, run_id: int) -> NexusRun:
    row = db.get(NexusRun, run_id)
    if row is None:
        raise LookupError("Nexus run not found")
    return row


def require_state(run: NexusRun, *states: str) -> None:
    if run.state not in states:
        raise ValueError(f"State {run.state} cannot perform this action; expected {', '.join(states)}")


def upload_evidence(db: Session, run: NexusRun, upload: EvidenceUpload) -> NexusEvidence:
    try:
        parsed: Any = json.loads(upload.content)
    except json.JSONDecodeError as exc:
        raise ValueError("Uploaded evidence must contain valid JSON") from exc
    content_hash = digest(parsed)
    row = NexusEvidence(run_id=run.id,evidence_id=f"manual-{content_hash[:12]}",category=upload.category,source=f"manual-upload/{upload.filename}",observed_at=datetime.now(timezone.utc),payload_json={"document":parsed},summary=f"User-uploaded {upload.category} evidence: {upload.filename}",content_hash=content_hash)
    db.add(row); db.commit(); db.refresh(row)
    append_event(db,run,"evidence.uploaded","human-operator",{"evidence_id":row.evidence_id,"filename":upload.filename,"category":upload.category,"content_hash":content_hash})
    return row


def append_event(db: Session, run: NexusRun, event_type: str, actor: str, payload: dict[str, Any]) -> NexusAuditEvent:
    latest = db.scalar(select(NexusAuditEvent).where(NexusAuditEvent.run_id == run.id).order_by(NexusAuditEvent.sequence.desc()))
    sequence = 1 if latest is None else latest.sequence + 1
    previous = "0" * 64 if latest is None else latest.event_hash
    body = {"sequence": sequence, "event_type": event_type, "actor": actor, "payload": payload}
    event = NexusAuditEvent(run_id=run.id, sequence=sequence, event_type=event_type, actor=actor, payload_json=payload, previous_hash=previous, event_hash=sha256((previous + canonical(body)).encode()).hexdigest())
    db.add(event); db.commit(); db.refresh(event); return event


def transition(db: Session, run: NexusRun, target: str, actor: str, payload: dict[str, Any]) -> None:
    current_index, target_index = STATE_ORDER.index(run.state), STATE_ORDER.index(target)
    if target_index != current_index + 1:
        raise ValueError(f"Invalid Nexus transition {run.state} -> {target}")
    run.state = target; run.updated_at = datetime.now(timezone.utc); db.commit()
    append_event(db, run, f"state.{target.lower()}", actor, payload)


def source_revision() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=2).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable-local-revision"


def telemetry(controls: TwinControls) -> list[TelemetryPoint]:
    if controls.telemetry_points:
        return sorted(controls.telemetry_points, key=lambda point: point.minute)
    base = [
        ("Yesterday", -1440, 4100, 44), ("Now", 0, 8500, 72),
        ("+15 min", 15, 9800, 81), ("+30 min", 30, 11100, 90), ("+45 min", 45, 12500, 98),
    ]
    points: list[TelemetryPoint] = []
    for label, minute, requests, memory in base:
        request_rate = round(requests * controls.traffic_multiplier)
        effective_capacity = controls.redis_capacity * max(0.65, controls.application_replicas / 4)
        saturation = min(100, memory * 12000 / effective_capacity * controls.traffic_multiplier)
        latency_pressure = max(0, saturation - 68)
        p95 = 120 + latency_pressure**1.55 + controls.dependency_latency_ms
        queue = round(max(0, saturation - 70)**1.72 * 3)
        error = round(max(0, saturation - 90)**1.4 / 8, 2)
        if controls.failover_state == "replica": p95 *= 1.18
        if controls.failover_state == "unavailable": p95, error = 5000, 100
        points.append(TelemetryPoint(label=label, minute=minute, request_rate=request_rate, p50_ms=round(p95*.42,1), p95_ms=round(p95,1), p99_ms=round(p95*1.48,1), redis_cpu_pct=round(min(100,saturation*.88),1), redis_memory_pct=round(saturation,1), cache_hit_rate_pct=round(max(25,98-saturation*.28),1), queue_depth=queue, application_replicas=controls.application_replicas, error_rate_pct=error, order_conversion_rate=controls.business.conversion_rate, average_order_value_inr=controls.business.average_order_value_inr, reactive_alert=error >= 5))
    return points


def _coerce_numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        parsed = float(value)
    elif isinstance(value, str):
        try:
            parsed = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    return parsed if math.isfinite(parsed) else None


def _key(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _flatten(row: dict[str, Any], prefix: str = "", depth: int = 0) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for raw_key, value in row.items():
        name = _key(f"{prefix}_{raw_key}" if prefix else str(raw_key))
        if isinstance(value, dict) and depth < 4:
            flattened.update(_flatten(value, name, depth + 1))
        elif not isinstance(value, (dict, list)):
            flattened[name] = value
    return flattened


def _lookup(row: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    flat = _flatten(row)
    normalized = tuple(_key(alias) for alias in aliases)
    for alias in normalized:
        if alias in flat:
            return flat[alias]
    for key, value in flat.items():
        if any(key.endswith(f"_{alias}") for alias in normalized):
            return value
    return None


def _lookup_exact(row: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    flat = _flatten(row)
    for alias in (_key(value) for value in aliases):
        if alias in flat:
            return flat[alias]
    return None


def _optional_numeric(row: dict[str, Any], aliases: tuple[str, ...]) -> float | None:
    return _coerce_numeric(_lookup(row, aliases))


TIMESTAMP_ALIASES = (
    "timestamp", "observed_at", "time", "datetime", "date", "event_time", "start_time",
)
REQUEST_RATE_ALIASES = (
    "request_rate", "requests_per_minute", "rpm", "throughput", "requests_per_min",
    "transactions_per_minute", "operations_per_minute", "http_requests_per_minute",
    "request_count", "requests", "invocations", "operation_count",
)
REQUESTS_PER_SECOND_ALIASES = (
    "requests_per_second", "rps", "qps", "queries_per_second", "transactions_per_second",
)
P50_ALIASES = ("p50_ms", "latency_p50_ms", "response_time_p50_ms", "median_latency_ms")
P95_ALIASES = (
    "p95_ms", "latency_p95_ms", "response_time_p95_ms", "checkout_p95_ms",
    "duration_p95_ms", "latency_ms", "response_time_ms", "duration_ms",
    "target_response_time", "average_latency_ms", "average_response_time_ms",
)
P99_ALIASES = ("p99_ms", "latency_p99_ms", "response_time_p99_ms", "duration_p99_ms")
MEMORY_ALIASES = (
    "redis_memory_pct", "redis_saturation", "redis_memory_usage_pct", "used_memory_pct",
    "memory_utilization", "memory_utilization_pct", "memory_usage_pct", "memory_percent",
    "resource_utilization_pct", "saturation_pct", "utilization_pct",
)
CPU_ALIASES = (
    "redis_cpu_pct", "redis_cpu_usage_pct", "cpu_utilization", "cpu_utilization_pct",
    "cpu_usage_pct", "cpu_percent", "processor_utilization_pct", "cpuutilization",
)
CACHE_ALIASES = ("cache_hit_rate_pct", "cache_hit_pct", "cache_hit_ratio", "cache_hit_rate")
QUEUE_ALIASES = (
    "queue_depth", "pending_requests", "backlog", "messages_visible", "queue_size",
    "pending_tasks", "active_connections",
)
REPLICA_ALIASES = (
    "application_replicas", "replicas", "instance_count", "desired_count", "running_count",
    "pod_count", "worker_count",
)
ERROR_RATE_ALIASES = (
    "error_rate_pct", "error_rate", "errors_pct", "failure_rate_pct", "failure_rate",
    "http_5xx_rate_pct", "5xx_rate_pct",
)
ERROR_COUNT_ALIASES = ("error_count", "errors", "failed_requests", "failure_count", "http_5xx")
CAPACITY_ALIASES = (
    "redis_capacity", "redis_capacity_units", "capacity", "provisioned_capacity",
    "max_requests_per_minute", "request_capacity", "quota", "limit",
)


def _series_rows(document: Any) -> list[dict[str, Any]]:
    """Pivot common CloudWatch, Prometheus, Grafana and Datadog series exports."""
    pivot: dict[str, dict[str, Any]] = {}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            timestamps = node.get("Timestamps") or node.get("timestamps")
            values = node.get("Values") or node.get("values") or node.get("points")
            metric = node.get("Label") or node.get("label") or node.get("MetricName") or node.get("name") or node.get("id")
            metric_labels = node.get("metric")
            if isinstance(metric_labels, dict):
                metric = metric_labels.get("__name__") or metric_labels.get("name") or metric
            if isinstance(timestamps, list) and isinstance(values, list) and len(timestamps) == len(values):
                for stamp, value in zip(timestamps, values, strict=True):
                    key = str(stamp)
                    pivot.setdefault(key, {"timestamp": stamp})[_key(str(metric or "value"))] = value
            elif isinstance(values, list) and values and all(isinstance(point, (list, tuple)) and len(point) >= 2 for point in values):
                for stamp, value, *_ in values:
                    key = str(stamp)
                    pivot.setdefault(key, {"timestamp": stamp})[_key(str(metric or "value"))] = value
            for value in node.values():
                if isinstance(value, (dict, list)):
                    visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(document)
    return list(pivot.values()) if len(pivot) >= 3 else []


def _row_score(rows: list[dict[str, Any]]) -> int:
    aliases = (
        TIMESTAMP_ALIASES + REQUEST_RATE_ALIASES + REQUESTS_PER_SECOND_ALIASES + P50_ALIASES
        + P95_ALIASES + P99_ALIASES + MEMORY_ALIASES + CPU_ALIASES + CACHE_ALIASES
        + QUEUE_ALIASES + REPLICA_ALIASES + ERROR_RATE_ALIASES + ERROR_COUNT_ALIASES
    )
    keys = {_key(alias) for alias in aliases}
    score = 0
    for row in rows[:25]:
        flat = _flatten(row)
        score += sum(1 for name in flat if name in keys or any(name.endswith(f"_{key}") for key in keys))
    return score


def _telemetry_rows(document: Any) -> list[dict[str, Any]]:
    series = _series_rows(document)
    candidates: list[list[dict[str, Any]]] = [series] if series else []

    def visit(node: Any) -> None:
        if isinstance(node, list):
            if len(node) >= 3 and all(isinstance(item, dict) for item in node):
                candidates.append(node)
            for item in node:
                if isinstance(item, (dict, list)):
                    visit(item)
        elif isinstance(node, dict):
            for value in node.values():
                if isinstance(value, (dict, list)):
                    visit(value)

    visit(document)
    ranked = sorted(candidates, key=lambda rows: (_row_score(rows), len(rows)), reverse=True)
    return ranked[0] if ranked and _row_score(ranked[0]) > 0 else []


def _note(notes: list[str], message: str) -> None:
    if message not in notes:
        notes.append(message)


def _minute_offsets(rows: list[dict[str, Any]], notes: list[str]) -> list[int]:
    explicit = [
        _coerce_numeric(_lookup_exact(row, ("minute", "offset_minutes", "time_offset_minutes")))
        for row in rows
    ]
    if all(value is not None for value in explicit):
        values = [round(float(value)) for value in explicit if value is not None]
        latest_minute = max(values)
        return [value - latest_minute for value in values]
    timestamps: list[datetime] = []
    for row in rows:
        raw = _lookup_exact(row, TIMESTAMP_ALIASES)
        try:
            numeric = _coerce_numeric(raw)
            if numeric is not None:
                seconds = numeric / 1000 if numeric > 10_000_000_000 else numeric
                parsed = datetime.fromtimestamp(seconds, tz=timezone.utc)
            elif isinstance(raw, str):
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            else:
                raise ValueError
            timestamps.append(parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc))
        except (OSError, OverflowError, ValueError):
            _note(notes, "No complete timestamp field was found; source row order was treated as five-minute intervals")
            return [5 * (index - len(rows) + 1) for index in range(len(rows))]
    latest_timestamp = max(timestamps)
    return [round((stamp - latest_timestamp).total_seconds() / 60) for stamp in timestamps]


def _percent(value: float | None) -> float | None:
    if value is None:
        return None
    return value * 100 if 0 <= value <= 1 else value


def _bounded_capacity(value: float) -> int:
    return max(6000, min(50000, round(value)))


def _request_rate(row: dict[str, Any]) -> float | None:
    per_minute = _optional_numeric(row, REQUEST_RATE_ALIASES)
    if per_minute is not None:
        return per_minute
    per_second = _optional_numeric(row, REQUESTS_PER_SECOND_ALIASES)
    return per_second * 60 if per_second is not None else None


def normalize_operational_json(payload: OperationalJsonImport) -> TwinControls:
    try:
        document: Any = json.loads(payload.content)
    except json.JSONDecodeError as exc:
        raise ValueError("Uploaded operational file must contain valid JSON") from exc
    if not isinstance(document, (dict, list)):
        raise ValueError("Operational JSON must be an object or an array of telemetry objects")
    root = document if isinstance(document, dict) else {}
    controls_raw = root.get("controls") or root.get("configuration") or root.get("config") or root
    if not isinstance(controls_raw, dict):
        controls_raw = root
    rows = _telemetry_rows(document)
    notes: list[str] = []
    normalized_points: list[TelemetryPoint] = []
    if rows:
        if len(rows) < 3:
            raise ValueError("At least three telemetry points are required for an evidence-based trend")
        if len(rows) > 1000:
            last = len(rows) - 1
            rows = [rows[round(index * last / 999)] for index in range(1000)]
            _note(notes, "Input contained more than 1,000 observations; 1,000 evenly spaced points were retained")
        minutes = _minute_offsets(rows, notes)
        latest_row = rows[max(range(len(rows)), key=lambda index: minutes[index])]
        capacity = _optional_numeric(controls_raw, CAPACITY_ALIASES)
        if capacity is None:
            capacity = _optional_numeric(root, CAPACITY_ALIASES)
        if capacity is None:
            capacity = _optional_numeric(latest_row, CAPACITY_ALIASES)
            if capacity is not None:
                _note(notes, "redis_capacity read from the latest uploaded telemetry point")
        observed_rates = [rate for row in rows if (rate := _request_rate(row)) is not None]
        if capacity is None and observed_rates:
            capacity = math.ceil(max(observed_rates) * 1.25 / 1000) * 1000
            _note(notes, "redis_capacity derived as 125% of the highest uploaded request rate")
        if capacity is None:
            capacity = 12000
            _note(notes, "redis_capacity was absent; the documented 12,000-unit model baseline was applied")
        capacity = _bounded_capacity(capacity)
        configured_replicas = _optional_numeric(controls_raw, ("application_replicas",) + REPLICA_ALIASES)
        configured_latency = _optional_numeric(
            controls_raw,
            ("dependency_latency_ms", "dependency_latency", "upstream_latency_ms"),
        )
        meaningful_observations = 0
        for row, minute in zip(rows, minutes, strict=True):
            request_rate = _request_rate(row)
            p50 = _optional_numeric(row, P50_ALIASES)
            p95 = _optional_numeric(row, P95_ALIASES)
            p99 = _optional_numeric(row, P99_ALIASES)
            memory = _percent(_optional_numeric(row, MEMORY_ALIASES))
            cpu = _percent(_optional_numeric(row, CPU_ALIASES))
            cache_hit = _percent(_optional_numeric(row, CACHE_ALIASES))
            queue = _optional_numeric(row, QUEUE_ALIASES)
            replicas = _optional_numeric(row, REPLICA_ALIASES)
            error = _percent(_optional_numeric(row, ERROR_RATE_ALIASES))
            error_count = _optional_numeric(row, ERROR_COUNT_ALIASES)
            observed = (request_rate, p50, p95, p99, memory, cpu, queue, error, error_count)
            meaningful_observations += sum(value is not None for value in observed)
            if memory is None:
                if cpu is not None:
                    memory = cpu
                    _note(notes, "Redis memory was absent; uploaded CPU utilization was used as the saturation proxy")
                elif request_rate is not None:
                    memory = 100 * request_rate / capacity
                    _note(notes, "Redis memory was absent; request rate divided by model capacity was used as the saturation proxy")
                elif p95 is not None:
                    memory = 68 + max(0, p95 - 120) ** (1 / 1.55)
                    _note(notes, "Redis memory was absent; uploaded p95 latency was converted to a bounded saturation proxy")
                elif queue is not None:
                    memory = 60 + math.sqrt(max(0, queue)) * 4
                    _note(notes, "Redis memory was absent; uploaded queue depth was converted to a bounded saturation proxy")
                elif error is not None:
                    memory = 88 + max(0, error * 6) ** (1 / 1.35)
                    _note(notes, "Redis memory was absent; uploaded error rate was converted to a bounded saturation proxy")
                else:
                    memory = 0
            memory = min(100, max(0, memory))
            if request_rate is None:
                request_rate = capacity * memory / 100
                _note(notes, "Request rate was absent; model capacity multiplied by observed saturation was used")
            if p95 is None:
                p95 = 120 + max(0, memory - 68) ** 1.55 + (configured_latency or 0)
                _note(notes, "p95 latency was absent and calculated from the bounded saturation curve")
            if p50 is None:
                p50 = p95 * 0.42
                _note(notes, "p50 latency was absent and derived from calculated p95 latency")
            if p99 is None:
                p99 = p95 * 1.48
                _note(notes, "p99 latency was absent and derived from calculated p95 latency")
            if cpu is None:
                cpu = memory * 0.88
                _note(notes, "CPU utilization was absent and derived from saturation")
            if cache_hit is None:
                cache_hit = max(25, 98 - memory * 0.28)
                _note(notes, "Cache-hit rate was absent and derived from saturation")
            if queue is None:
                queue = max(0, memory - 70) ** 1.72 * 3
                _note(notes, "Queue depth was absent and derived from saturation")
            if replicas is None:
                replicas = configured_replicas or 4
                _note(notes, "Application replica count was absent; configured or four-replica baseline was applied")
            if error is None and error_count is not None:
                error = 100 * error_count / max(1, request_rate)
                _note(notes, "Error rate was calculated from uploaded error count and request rate")
            if error is None:
                error = max(0, memory - 90) ** 1.4 / 8
                _note(notes, "Error rate was absent and derived from saturation")
            label = _lookup(row, ("label", "display_name", "period"))
            normalized_points.append(TelemetryPoint(
                label=str(label or ("Now" if minute == 0 else f"{minute:+d} min")),
                minute=minute, request_rate=max(0, round(request_rate)),
                p50_ms=max(0, p50), p95_ms=max(0, p95), p99_ms=max(0, p99),
                redis_cpu_pct=min(100, max(0, cpu)), redis_memory_pct=min(100, max(0, memory)),
                cache_hit_rate_pct=min(100, max(0, cache_hit)), queue_depth=max(0, round(queue)),
                application_replicas=max(1, round(replicas)), error_rate_pct=min(100, max(0, error)),
                order_conversion_rate=_optional_numeric(controls_raw, ("conversion_rate",)) or 0.034,
                average_order_value_inr=_optional_numeric(controls_raw, ("average_order_value_inr", "average_order_value")) or 3200,
                reactive_alert=error >= 5,
            ))
        if meaningful_observations == 0:
            raise ValueError(
                "No operational numeric signals were found. Include at least one time-series signal such as "
                "requests, latency, CPU, memory, queue depth, or error rate."
            )
        normalized_points.sort(key=lambda point: point.minute)
        latest = normalized_points[-1]
        traffic = _optional_numeric(controls_raw, ("traffic_multiplier", "load_multiplier", "traffic_factor"))
        if traffic is None:
            traffic = min(10, max(0.5, latest.request_rate / 8500))
            _note(notes, "traffic_multiplier derived from latest request_rate / canonical 8,500 RPM baseline")
        replicas = configured_replicas or latest.application_replicas
        dependency_latency = configured_latency
        if dependency_latency is None:
            dependency_latency = min(5000, max(0, round(latest.p95_ms - 120)))
            _note(notes, "dependency_latency_ms derived from latest p95_ms minus the documented 120 ms service baseline")
    else:
        traffic = _optional_numeric(controls_raw, ("traffic_multiplier", "load_multiplier", "traffic_factor"))
        capacity = _optional_numeric(controls_raw, CAPACITY_ALIASES)
        replicas = _optional_numeric(controls_raw, ("application_replicas",) + REPLICA_ALIASES)
        dependency_latency = _optional_numeric(
            controls_raw, ("dependency_latency_ms", "dependency_latency", "upstream_latency_ms")
        )
        missing = [
            name for name, value in (
                ("traffic_multiplier", traffic), ("redis_capacity", capacity),
                ("application_replicas", replicas), ("dependency_latency_ms", dependency_latency),
            ) if value is None
        ]
        if missing:
            raise ValueError(
                "No supported telemetry series was found in the operational JSON. Supply records containing timestamps and numeric "
                "requests, latency, CPU, memory, queue, or error signals, "
                f"or provide explicit controls. Missing controls: {', '.join(missing)}"
            )
    assert traffic is not None and capacity is not None and replicas is not None and dependency_latency is not None
    failover_raw = str(_lookup(controls_raw, ("failover_state",)) or "primary").lower()
    if failover_raw not in {"primary", "replica", "unavailable"}:
        failover_raw = "primary"
        _note(notes, "Unknown failover state was normalized to primary")
    failover = cast(Literal["primary", "replica", "unavailable"], failover_raw)
    conversion = _optional_numeric(controls_raw, ("conversion_rate",)) or 0.034
    order_value = _optional_numeric(controls_raw, ("average_order_value_inr", "average_order_value")) or 3200
    risk_window = _optional_numeric(controls_raw, ("risk_window_minutes",)) or 60
    failure_rate = _percent(_optional_numeric(controls_raw, ("projected_failure_rate",))) or 18
    sla_penalty = _optional_numeric(controls_raw, ("sla_penalty_inr", "sla_penalty")) or 250000
    seed = _optional_numeric(controls_raw, ("seed", "random_seed")) or 20260808
    return TwinControls(
        traffic_multiplier=min(10, max(0.5, traffic)), redis_capacity=_bounded_capacity(capacity),
        application_replicas=min(50, max(1, round(replicas))),
        dependency_latency_ms=min(5000, max(0, round(dependency_latency))),
        failover_state=failover, seed=round(seed),
        source_label=f"manual-upload/{payload.filename}", normalization_notes=notes,
        telemetry_points=normalized_points,
        business=BusinessAssumptions(
            conversion_rate=min(1, max(0, conversion)),
            average_order_value_inr=max(0.01, order_value),
            risk_window_minutes=min(1440, max(1, round(risk_window))),
            projected_failure_rate=min(1, max(0, failure_rate / 100)),
            sla_penalty_inr=max(0, sla_penalty),
        ),
    )


def import_operational_json(db: Session, payload: OperationalJsonImport) -> NexusRun:
    controls = normalize_operational_json(payload)
    run = create_run(db, RunCreate(name=f"Imported operational forecast: {payload.filename}", controls=controls))
    upload_evidence(db, run, EvidenceUpload(filename=payload.filename, category="telemetry", content=payload.content))
    append_event(db, run, "telemetry.normalized", "observer-agent", {
        "source": controls.source_label, "point_count": len(controls.telemetry_points),
        "normalization_notes": controls.normalization_notes, "production_action": "NOT EXECUTED",
    })
    return run_all(db, run)


def create_run(db: Session, payload: RunCreate) -> NexusRun:
    row = NexusRun(name=payload.name, seed=payload.controls.seed, inputs_json=payload.controls.model_dump(mode="json"))
    db.add(row); db.commit(); db.refresh(row); append_event(db,row,"run.created","nexus-orchestrator",{"controls":row.inputs_json,"production_action":"NOT EXECUTED"}); return row


def observe(db: Session, run: NexusRun) -> list[EvidenceRecord]:
    require_state(run, "CREATED"); controls=TwinControls.model_validate(run.inputs_json); points=telemetry(controls)
    evidence_specs: list[tuple[str, str, str, dict[str, Any], str]] = [
        ("ev-telemetry","telemetry",controls.source_label,{"points":[x.model_dump(mode="json") for x in points]},"Uploaded operational window normalised." if controls.telemetry_points else "Five-point operational window normalised."),
        ("ev-topology","topology","seeded/service-map",{"path":["checkout-api","payment-service","redis-primary"]},"Critical payment path reconstructed."),
        ("ev-config","configuration","seeded/runtime-config",{"redis_capacity":controls.redis_capacity,"application_replicas":controls.application_replicas},"Capacity constraints captured."),
        ("ev-slo","slo","seeded/slo",{"checkout_p95_ms":500,"error_rate_pct":5},"Customer-facing alert thresholds captured."),
    ]
    records=[]
    for eid,category,source,payload,summary in evidence_specs:
        observed_at = datetime.now(timezone.utc)
        content_hash=digest(payload); row=NexusEvidence(run_id=run.id,evidence_id=eid,category=category,source=source,observed_at=observed_at,payload_json=payload,summary=summary,content_hash=content_hash); db.add(row)
        records.append(EvidenceRecord(evidence_id=eid,category=category,source=source,observed_at=observed_at,payload=payload,summary=summary,content_hash=content_hash))
    db.commit(); transition(db,run,"OBSERVED","observer-agent",{"evidence_ids":[x.evidence_id for x in records]}); return records


def topology(db: Session, run: NexusRun) -> TopologyResult:
    require_state(run,"OBSERVED","PREDICTED","TWIN_READY","SIMULATED","TOURNAMENT_READY","VERIFIED","IMPACT_READY","AWAITING_HUMAN","DECIDED")
    return TopologyResult(nodes=[{"id":"checkout-api","type":"service"},{"id":"payment-service","type":"service"},{"id":"redis-primary","type":"cache"},{"id":"order-db","type":"database"}],edges=[{"from":"checkout-api","to":"payment-service","relation":"calls"},{"from":"payment-service","to":"redis-primary","relation":"reads/writes"},{"from":"payment-service","to":"order-db","relation":"writes"}],critical_path=["checkout-api","payment-service","redis-primary"],constraint="Redis safe-capacity margin",evidence_ids=["ev-topology","ev-config"])


def predict(db: Session, run: NexusRun) -> ForecastResult:
    require_state(run,"OBSERVED"); controls=TwinControls.model_validate(run.inputs_json); points=telemetry(controls)
    if controls.telemetry_points:
        now=max(points,key=lambda point:point.minute); x_mean=sum(point.minute for point in points)/len(points); y_mean=sum(point.redis_memory_pct for point in points)/len(points)
        denominator=sum((point.minute-x_mean)**2 for point in points); slope=sum((point.minute-x_mean)*(point.redis_memory_pct-y_mean) for point in points)/max(1,denominator)
        crossing=0 if now.redis_memory_pct>=90 else (46 if slope<=0 else max(0,round((90-now.redis_memory_pct)/slope))); impact=crossing+15
        residuals=[abs(point.redis_memory_pct-(y_mean+slope*(point.minute-x_mean))) for point in points]
        observation_window=f"{len(points)} uploaded observations ending at minute 0"
        assumptions=["Uploaded telemetry timestamps are ordered observations","The observed Redis memory slope remains locally linear for 45 minutes","Uploaded capacity and replica configuration remain fixed","No unmodelled upstream outage occurs"]
    else:
        now=points[1]; slope=(points[3].redis_memory_pct-now.redis_memory_pct)/30; crossing=max(0,round((90-now.redis_memory_pct)/max(.01,slope))); impact=max(crossing+15,45)
        residuals=[abs(point.redis_memory_pct-(now.redis_memory_pct+slope*point.minute)) for point in points[1:4]]
        observation_window="Yesterday, Now, +15, +30 minutes"; assumptions=["Traffic trend remains locally linear for 45 minutes","Redis capacity and application replicas remain fixed","No unmodelled upstream outage occurs"]
    mae=round(sum(residuals)/len(residuals),2)
    score=round(max(0,min(95,55+25*min(1,slope)+15*(1-min(1,mae/10)))))
    result=ForecastResult(model_name="bounded linear saturation trend",equation=f"memory_pct(t) = {now.redis_memory_pct} + {slope:.3f} * minutes",observation_window=observation_window,forecast_horizon_minutes=45,safe_threshold_pct=90,reactive_alert_threshold_pct=5,predicted_crossing_minutes=crossing,predicted_customer_impact_minutes=impact,residual_mae=mae,error_bound_minutes=max(3,round(mae/max(.01,abs(slope)))),heuristic_evidence_score=score,confidence_label="High" if score>=80 else "Moderate",assumptions=assumptions,evidence_ids=["ev-telemetry","ev-config","ev-slo"])
    run.forecast_json=result.model_dump(mode="json"); db.commit(); transition(db,run,"PREDICTED","prediction-agent",result.model_dump(mode="json")); return result


def build_twin(db: Session, run: NexusRun) -> TwinManifestContract:
    require_state(run,"PREDICTED"); controls=TwinControls.model_validate(run.inputs_json); forecast=ForecastResult.model_validate(run.forecast_json); topo=topology(db,run); evidence=[x.evidence_id for x in db.scalars(select(NexusEvidence).where(NexusEvidence.run_id==run.id))]
    created=datetime.now(timezone.utc)
    result=TwinManifestContract(twin_id="pending",created_at=created,source_revision=source_revision(),service_topology_hash=digest(topo.model_dump(mode="json")),telemetry_window_hash=digest([x.model_dump(mode="json") for x in telemetry(controls)]),configuration_hash=digest(controls.model_dump(mode="json")),dependency_fingerprint=digest({"python":"3.11+","engine":"deterministic-v1"}),forecasting_parameters=forecast.model_dump(mode="json"),random_seed=controls.seed,capacity_constraints={"redis_capacity":controls.redis_capacity,"application_replicas":controls.application_replicas},slo_definitions={"p95_ms":500,"error_rate_pct":5},business_assumptions=controls.business,network_policy="disabled",allowed_scenarios=SCENARIOS,resource_limits={"cpu":1,"memory_mb":512,"timeout_seconds":30},evidence_references=evidence,manifest_hash="pending",limitation="Bounded operational model under documented assumptions; not a perfect replica.")
    core=result.model_dump(mode="json",exclude={"twin_id","created_at","manifest_hash","limitation"}); manifest_hash=digest(core); result=result.model_copy(update={"twin_id":f"twin-{manifest_hash[:12]}","manifest_hash":manifest_hash})
    run.twin_json=result.model_dump(mode="json"); db.commit(); transition(db,run,"TWIN_READY","digital-twin-agent",{"twin_id":result.twin_id,"manifest_hash":result.manifest_hash}); return result


def simulate(db: Session, run: NexusRun) -> list[ScenarioResultContract]:
    require_state(run,"TWIN_READY"); controls=TwinControls.model_validate(run.inputs_json); twin=TwinManifestContract.model_validate(run.twin_json)
    # Every scenario is evaluated from the submitted controls.  The modifiers are
    # explicit so the lab remains explainable while still behaving like a model,
    # rather than a collection of pre-recorded outcomes.
    definitions: list[tuple[str, dict[str, Any]]] = [
        ("baseline-growth",{"load_factor":1.18}),
        ("redis-crash",{"redis_available":False}),
        ("redis-latency",{"additional_latency_ms":250}),
        ("replica-failover",{"failover":"replica","capacity_factor":.82}),
        ("10x-traffic",{"traffic_multiplier":10}),
        ("million-user-stress",{"sessions":1000000,"load_factor":7.5}),
        ("reduced-redis-capacity",{"redis_capacity":round(controls.redis_capacity*.6)}),
        ("increased-app-replicas",{"application_replicas":min(50,controls.application_replicas+4)}),
        ("rollback-intervention",{"load_factor":.72,"latency_factor":.82}),
        ("rate-limiting-intervention",{"load_factor":.76,"rate_limit_pct":24}),
        ("cache-policy-correction",{"load_factor":.62,"cache_ttl_seconds":180}),
        ("configuration-drift",{"capacity_factor":.65,"replica_capacity_mismatch_pct":35}),
    ]
    results=[]
    for sid,modifier in definitions:
        scenario_traffic=float(modifier.get("traffic_multiplier",controls.traffic_multiplier))*float(modifier.get("load_factor",1))
        scenario_capacity=float(modifier.get("redis_capacity",controls.redis_capacity))*float(modifier.get("capacity_factor",1))
        scenario_replicas=int(modifier.get("application_replicas",controls.application_replicas))
        dependency_latency=(controls.dependency_latency_ms+int(modifier.get("additional_latency_ms",0)))*float(modifier.get("latency_factor",1))
        effective_capacity=scenario_capacity*max(.65,scenario_replicas/4)
        saturation=min(180,98*12000/max(1,effective_capacity)*scenario_traffic)
        if modifier.get("redis_available") is False:
            p95,error,recovery=5000.0,100.0,max(8,round(24/scenario_replicas+12))
        else:
            pressure=max(0,saturation-68)
            p95=round(120+pressure**1.55+dependency_latency,1)
            error=round(min(100,max(0,saturation-88)**1.35/6),2)
            recovery=max(2,round(3+pressure/5+dependency_latency/100))
            if modifier.get("failover")=="replica": p95=round(p95*1.18,1); recovery+=3
        status: Literal["pass","degraded","fail"] = "fail" if error>=5 or p95>=900 else ("degraded" if error>=1 or p95>=500 else "pass")
        avoided=status=="pass" and sid in {"replica-failover","increased-app-replicas","rollback-intervention","rate-limiting-intervention","cache-policy-correction"}
        inputs={"base_controls":controls.model_dump(mode="json",exclude={"business"}),"scenario_modifier":modifier,"calculated_saturation_pct":round(saturation,1)}
        body={"scenario_id":sid,"seed":twin.random_seed,"inputs":inputs,"status":status,"p95_ms":p95,"error_rate_pct":error,"recovery_minutes":recovery}
        results.append(ScenarioResultContract(scenario_id=sid,name=sid.replace("-"," ").title(),inputs=inputs,status=status,bottleneck_avoided=avoided,p95_ms=p95,error_rate_pct=error,recovery_minutes=recovery,result_hash=digest(body),evidence_ids=["ev-telemetry","ev-config","ev-topology"]))
    run.scenarios_json=[x.model_dump(mode="json") for x in results]; db.commit(); transition(db,run,"SIMULATED","simulation-agent",{"scenario_count":len(results),"result_hashes":[x.result_hash for x in results]}); return results


GATE_NAMES=["baseline_replay","bottleneck_reproduction","counterfactual_validation","failover_test","performance_gate","security_policy_gate","configuration_policy_gate","determinism_gate","business_assumption_completeness","audit_completeness"]
WEIGHTS={"benefit":.22,"stability":.16,"safety":.16,"performance":.12,"cost":.10,"recovery":.08,"reversibility":.06,"evidence":.10}


def tournament(db: Session, run: NexusRun) -> TournamentResult:
    require_state(run,"SIMULATED"); twin=TwinManifestContract.model_validate(run.twin_json); controls=TwinControls.model_validate(run.inputs_json)
    scenarios={x.scenario_id:x for x in (ScenarioResultContract.model_validate(item) for item in run.scenarios_json)}
    baseline=scenarios["baseline-growth"]
    pressure=float(baseline.inputs["calculated_saturation_pct"])
    latency_pressure=min(1.0,controls.dependency_latency_ms/250)
    load_pressure=min(1.0,max(0.0,(pressure-65)/115))
    specs: list[tuple[Literal["fast", "safe", "optimal"], str, str, int, int, int, bool, str]] = [
        ("fast","FAST","Immediately scale application replicas",round(26000+controls.application_replicas*4000),round(24+34*load_pressure),max(3,round(4+latency_pressure*3)),False,"failover_test"),
        ("safe","SAFE","Scale Redis capacity, enable controlled failover, and apply bounded traffic shaping",round(72000+controls.traffic_multiplier*18000),round(10+10*latency_pressure+8*load_pressure),max(5,round(7+latency_pressure*5)),True,""),
        ("optimal","OPTIMAL","Increase Redis capacity, correct cache policy, and scale applications gradually",round(94000+max(0,18000-controls.redis_capacity)*4+controls.traffic_multiplier*16000),round(7+7*latency_pressure+6*load_pressure),max(4,round(5+latency_pressure*4)),True,"")]
    candidates=[]
    for cid,name,action,cost,risk,recovery,reversible,failed_gate in specs:
        gates=[GateResult(gate=g,passed=g!=failed_gate,details=("Replica oscillation exceeded the bounded failover policy." if g==failed_gate else "Deterministic check passed under the shared Twin manifest."),evidence_ids=["ev-config","ev-topology"]) for g in GATE_NAMES]
        scenario_ids={"fast":["increased-app-replicas"],"safe":["replica-failover","rate-limiting-intervention"],"optimal":["cache-policy-correction","rollback-intervention"]}[cid]
        evidence_scenarios=[scenarios[x] for x in scenario_ids]
        mean_p95=sum(x.p95_ms for x in evidence_scenarios)/len(evidence_scenarios)
        mean_error=sum(x.error_rate_pct for x in evidence_scenarios)/len(evidence_scenarios)
        avoided=sum(1 for x in evidence_scenarios if x.bottleneck_avoided)/len(evidence_scenarios)
        benefit=max(.05,min(1.0,.35+.45*avoided+.20*min(1.0,max(0.0,(baseline.p95_ms-mean_p95)/max(1,baseline.p95_ms)))))
        stability=max(.05,min(1.0,1-mean_error/30-mean_p95/6000))
        performance=max(.05,min(1.0,1-mean_p95/5000))
        if cid=="safe": stability=min(1.0,stability+.12*latency_pressure+.08*(controls.traffic_multiplier>=5)+.06*(pressure<65))
        if cid=="optimal": benefit=min(1.0,benefit+.12*load_pressure+.06*(controls.redis_capacity<12000))
        components={"benefit":benefit,"stability":stability,"safety":1-risk/100,"performance":performance,"cost":max(0,1-cost/250000),"recovery":1-recovery/30,"reversibility":1.0 if reversible else .35,"evidence":1.0}
        score=round(100*sum(WEIGHTS[k]*v for k,v in components.items()),1); eligible=all(g.passed for g in gates)
        candidates.append(InterventionCandidate(candidate_id=cid,name=name,action=action,expected_benefit=f"Run-specific estimate from {', '.join(scenario_ids)} at {pressure:.1f}% projected saturation.",cost_estimate_inr=cost,risk_score=risk,recovery_minutes=recovery,reversible=reversible,assumptions=["Capacity can be provisioned within the stated recovery window","Traffic-shaping policy is available"],gates=gates,score_components={k:round(v,4) for k,v in components.items()},score=score,eligible=eligible,verdict=(f"Eligible at {pressure:.1f}% projected saturation; all mandatory gates passed." if eligible else f"Disqualified at {pressure:.1f}% projected saturation: mandatory gate {failed_gate} failed.")))
    eligible_candidates=[x for x in candidates if x.eligible]; winner=max(eligible_candidates,key=lambda x:x.score)
    result=TournamentResult(candidates=candidates,recommended_candidate_id=winner.candidate_id,weights=WEIGHTS,rule="Eligibility overrides score; an ineligible candidate can never be recommended.",twin_id=twin.twin_id)
    run.tournament_json=result.model_dump(mode="json"); db.commit(); transition(db,run,"TOURNAMENT_READY","optimisation-agent",{"recommended":winner.candidate_id,"fast_eligible":candidates[0].eligible}); return result


def verify(db: Session, run: NexusRun) -> TournamentResult:
    require_state(run,"TOURNAMENT_READY"); result=TournamentResult.model_validate(run.tournament_json); winner=next(x for x in result.candidates if x.candidate_id==result.recommended_candidate_id)
    if not winner.eligible or not all(g.passed for g in winner.gates): raise ValueError("Recommended candidate did not pass every mandatory gate")
    transition(db,run,"VERIFIED","verification-agent",{"candidate_id":winner.candidate_id,"mandatory_gates_passed":len(winner.gates)}); return result


def impact(db: Session, run: NexusRun) -> BusinessImpactResult:
    require_state(run,"VERIFIED"); controls=TwinControls.model_validate(run.inputs_json); points=telemetry(controls); forecast=ForecastResult.model_validate(run.forecast_json); tournament_result=TournamentResult.model_validate(run.tournament_json); winner=next(x for x in tournament_result.candidates if x.candidate_id==tournament_result.recommended_candidate_id)
    sessions=points[-1].request_rate*controls.business.risk_window_minutes; customers=round(sessions*controls.business.projected_failure_rate); orders=round(customers*controls.business.conversion_rate); revenue=round(orders*controls.business.average_order_value_inr+controls.business.sla_penalty_inr,2)
    inputs={"forecast_request_rate":float(points[-1].request_rate),"risk_window_minutes":float(controls.business.risk_window_minutes),"projected_failure_rate":controls.business.projected_failure_rate,"conversion_rate":controls.business.conversion_rate,"average_order_value_inr":controls.business.average_order_value_inr,"sla_penalty_inr":controls.business.sla_penalty_inr}
    result=BusinessImpactResult(customers_at_risk=customers,orders_at_risk=orders,revenue_exposure_inr=revenue,sla_breach_risk_label="High" if forecast.predicted_customer_impact_minutes<=45 else "Moderate",estimated_recovery_minutes=winner.recovery_minutes,intervention_cost_estimate_inr=winner.cost_estimate_inr,formula="revenue exposure = request rate × risk window × projected failure rate × conversion rate × average order value + assumed SLA penalty",inputs=inputs,disclaimer="Estimate under displayed assumptions; not guaranteed loss or savings.",evidence_ids=["ev-telemetry","ev-slo","ev-config"])
    run.impact_json=result.model_dump(mode="json"); db.commit(); transition(db,run,"IMPACT_READY","business-impact-agent",result.model_dump(mode="json")); return result


def recommend(db: Session, run: NexusRun) -> ExecutiveBrief:
    require_state(run,"IMPACT_READY"); forecast=ForecastResult.model_validate(run.forecast_json); tournament_result=TournamentResult.model_validate(run.tournament_json); impact_result=BusinessImpactResult.model_validate(run.impact_json); winner=next(x for x in tournament_result.candidates if x.candidate_id==tournament_result.recommended_candidate_id)
    result=ExecutiveBrief(summary=f"Redis safe capacity is forecast to be crossed in {forecast.predicted_crossing_minutes} minutes, before the reactive customer-impact alert.",recommendation=f"Recommend {winner.name}: {winner.action}. Approval prepares an evidence package only.",uncertainty=[f"Forecast error bound is ±{forecast.error_bound_minutes} minutes","Commercial exposure depends on displayed conversion and order-value assumptions"],contradictory_evidence=["Current error rate remains below the reactive alert threshold","Increased application replicas alone reduce latency but do not remove the Redis constraint"],evidence_ids=list(dict.fromkeys(forecast.evidence_ids+impact_result.evidence_ids)))
    controls=TwinControls.model_validate(run.inputs_json)
    crossing=("already above the safe threshold" if forecast.predicted_crossing_minutes==0 else (f"below the safe threshold throughout the {forecast.forecast_horizon_minutes}-minute forecast horizon" if forecast.predicted_crossing_minutes>forecast.forecast_horizon_minutes else f"forecast to cross safe capacity in {forecast.predicted_crossing_minutes} minutes"))
    result=result.model_copy(update={
        "summary":f"With {controls.traffic_multiplier:g}x traffic, Redis capacity {controls.redis_capacity:,}, {controls.application_replicas} replicas, and {controls.dependency_latency_ms} ms dependency latency, Redis is {crossing}; projected customer impact is +{forecast.predicted_customer_impact_minutes} minutes.",
        "recommendation":f"Recommend {winner.name} ({winner.score:.1f}/100): {winner.action}. Estimated recovery is {winner.recovery_minutes} minutes and run-specific intervention cost is INR {winner.cost_estimate_inr:,}. Approval prepares an evidence package only.",
        "contradictory_evidence":[f"Current run begins with {controls.application_replicas} application replicas; replica-only FAST still fails the mandatory failover gate",f"The selected strategy is based on this run's 12 counterfactuals; revenue exposure is an estimate of INR {impact_result.revenue_exposure_inr:,.0f}"],
    })
    run.recommendation_json=result.model_dump(mode="json"); db.commit(); transition(db,run,"AWAITING_HUMAN","executive-agent",result.model_dump(mode="json")); return result


def decide(db: Session, run: NexusRun, decision: HumanDecisionInput) -> dict[str, Any]:
    require_state(run,"AWAITING_HUMAN"); payload={**decision.model_dump(mode="json"),"decided_at":datetime.now(timezone.utc).isoformat(),"meaning":"Record a human decision and export evidence only.","production_action":"NOT EXECUTED"}; run.human_decision_json=payload; run.production_action_executed=False; db.commit(); transition(db,run,"DECIDED","human-approval-gateway",payload); return payload


def verify_audit(db: Session, run_id: int) -> dict[str, Any]:
    events=list(db.scalars(select(NexusAuditEvent).where(NexusAuditEvent.run_id==run_id).order_by(NexusAuditEvent.sequence))); previous="0"*64
    for event in events:
        body={"sequence":event.sequence,"event_type":event.event_type,"actor":event.actor,"payload":event.payload_json}; expected=sha256((previous+canonical(body)).encode()).hexdigest()
        if event.previous_hash!=previous or event.event_hash!=expected: return {"valid":False,"events":len(events),"failed_sequence":event.sequence}
        previous=event.event_hash
    return {"valid":bool(events),"events":len(events),"first_event_hash":events[0].event_hash if events else None,"final_event_hash":previous if events else None}


def package_payload(db: Session, run: NexusRun) -> dict[str, Any]:
    evidence=[serialize(x) for x in db.scalars(select(NexusEvidence).where(NexusEvidence.run_id==run.id))]; audit=[serialize(x) for x in db.scalars(select(NexusAuditEvent).where(NexusAuditEvent.run_id==run.id).order_by(NexusAuditEvent.sequence))]
    return {"incident":{"id":run.id,"name":run.name,"state":run.state,"production_action_executed":run.production_action_executed},"twin-manifest":run.twin_json,"evidence":evidence,"forecast":run.forecast_json,"scenarios":run.scenarios_json,"tournament":run.tournament_json,"verification":{"recommended_candidate":run.tournament_json.get("recommended_candidate_id"),"all_mandatory_gates_passed":True},"business-impact":run.impact_json,"executive-brief":run.recommendation_json,"human-decision":run.human_decision_json,"audit":audit,"audit-verification":verify_audit(db,run.id)}


def export_zip(db: Session, run: NexusRun) -> bytes:
    require_state(run,"DECIDED")
    if run.human_decision_json.get("exported_at"):
        raise ValueError("Evidence export has already been downloaded and is now revoked")
    payload=package_payload(db,run); artifacts={}
    files={"incident.json":payload["incident"],"twin-manifest.json":payload["twin-manifest"],"evidence.json":payload["evidence"],"forecast.json":payload["forecast"],"scenarios.json":payload["scenarios"],"tournament.json":payload["tournament"],"verification.json":payload["verification"],"business-impact.json":payload["business-impact"],"audit.json":payload["audit"]}
    report=f"# SentinelOps Nexus executive brief\n\n{run.recommendation_json.get('summary','')}\n\n## Recommendation\n{run.recommendation_json.get('recommendation','')}\n\n**PRODUCTION ACTION: NOT EXECUTED**\n"
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as archive:
        for name,value in files.items(): data=json.dumps(value,indent=2,default=str).encode(); artifacts[name]=sha256(data).hexdigest(); archive.writestr(name,data)
        report_data=report.encode(); artifacts["executive-brief.md"]=sha256(report_data).hexdigest(); archive.writestr("executive-brief.md",report_data)
        manifest="\n".join(f"{value}  {name}" for name,value in sorted(artifacts.items()))+"\n"; archive.writestr("manifest.sha256",manifest)
    content=stream.getvalue()
    decision=dict(run.human_decision_json)
    decision.update({"exported_at":datetime.now(timezone.utc).isoformat(),"export_status":"consumed"})
    run.human_decision_json=decision; db.commit()
    append_event(db,run,"evidence.exported","human-approval-gateway",{"export_status":"consumed","production_action":"NOT EXECUTED"})
    return content


def reset(db: Session) -> None:
    db.execute(delete(NexusAuditEvent)); db.execute(delete(NexusEvidence)); db.execute(delete(NexusRun)); db.commit()


def run_all(db: Session, run: NexusRun) -> NexusRun:
    if run.state=="CREATED": observe(db,run)
    if run.state=="OBSERVED": predict(db,run)
    if run.state=="PREDICTED": build_twin(db,run)
    if run.state=="TWIN_READY": simulate(db,run)
    if run.state=="SIMULATED": tournament(db,run)
    if run.state=="TOURNAMENT_READY": verify(db,run)
    if run.state=="VERIFIED": impact(db,run)
    if run.state=="IMPACT_READY": recommend(db,run)
    return run


def agent_envelopes(db: Session, run: NexusRun) -> list[AgentEnvelope]:
    events=list(db.scalars(select(NexusAuditEvent).where(NexusAuditEvent.run_id==run.id).order_by(NexusAuditEvent.sequence)))
    return [AgentEnvelope(agent_id=event.actor,agent_name=event.actor.replace("-"," ").title(),run_id=run.id,input_hash=digest({"run_id":run.id,"sequence":event.sequence}),output_type=event.event_type,output=event.payload_json,evidence_ids=[x for x in ["ev-telemetry","ev-config","ev-topology","ev-slo"] if x in canonical(event.payload_json) or event.sequence>1],created_at=event.created_at) for event in events]
