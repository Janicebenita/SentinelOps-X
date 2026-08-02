from __future__ import annotations

from hashlib import sha256
from typing import Any

AGENTS = [
    ("observe", "Observation Agent", "Telemetry window normalised"),
    ("evidence", "Evidence Agent", "Cross-signal evidence linked"),
    ("discover", "Process Discovery Agent", "Critical checkout path reconstructed"),
    ("predict", "Prediction Agent", "Capacity threshold crossing forecast"),
    ("twin", "Digital Twin Agent", "Isolated future-state manifest created"),
    ("simulate", "Simulation Agent", "Chaos and load scenarios replayed"),
    ("optimise", "Optimisation Agent", "Eligible interventions ranked"),
    ("impact", "Business Impact Agent", "Commercial exposure estimated"),
    ("executive", "Executive Agent", "Evidence-backed decision brief prepared"),
]


def digest(value: object) -> str:
    return sha256(repr(value).encode()).hexdigest()


def build_operational_twin(load_multiplier: float = 1.0, redis_capacity: int = 12000) -> dict[str, Any]:
    """Build the deterministic finale twin from explicit seeded assumptions."""
    if not 0.5 <= load_multiplier <= 4:
        raise ValueError("load_multiplier must be between 0.5 and 4.0")
    if not 6000 <= redis_capacity <= 30000:
        raise ValueError("redis_capacity must be between 6000 and 30000")

    minutes = [-30, -20, -10, 0, 10, 20, 30]
    requests = [round(v * load_multiplier) for v in [6200, 6900, 7700, 8500, 9600, 10800, 12100]]
    saturation = [round(min(100, v / redis_capacity * 100), 1) for v in requests]
    latency = [round(88 + max(0, v - 65) ** 1.72 / 5.6, 1) for v in saturation]
    queues = [round(max(0, v - 72) ** 1.8 * 2.4) for v in saturation]
    errors = [round(max(0, v - 88) ** 1.45 / 18, 2) for v in saturation]
    telemetry = [
        {"minute": minute, "requests_per_minute": request_rate, "redis_saturation": sat, "checkout_p95_ms": delay, "queue_depth": queue, "error_rate": error}
        for minute, request_rate, sat, delay, queue, error in zip(minutes, requests, saturation, latency, queues, errors, strict=True)
    ]

    crossing = next((minute for minute, sat in zip(minutes, saturation, strict=True) if minute >= 0 and sat >= 90), 30)
    evidence_coverage = 8 / 9
    signal_strength = min(1, max(0, (saturation[-1] - saturation[3]) / 35))
    confidence = round(100 * (0.55 * evidence_coverage + 0.45 * signal_strength))
    conversion_rate, average_order_value, risk_window = 0.034, 3200, 60
    exposed_customers = round(requests[5] * risk_window * conversion_rate)
    revenue_risk = exposed_customers * average_order_value

    evidence = [
        {"id": "ev-cache", "source": "redis_memory_saturation", "value": saturation[3], "claim": "Cache demand is rising faster than capacity."},
        {"id": "ev-queue", "source": "checkout_queue_depth", "value": queues[3], "claim": "Queue growth begins before customer-visible errors."},
        {"id": "ev-latency", "source": "checkout_p95_ms", "value": latency[3], "claim": "Latency remains within SLO but its gradient is worsening."},
        {"id": "ev-graph", "source": "dependency_graph", "value": "checkout → pricing → redis", "claim": "The payment path depends on the constrained cache."},
    ]
    strategies: list[dict[str, Any]] = [
        {"id": "fast", "name": "Fast", "action": "Scale Redis replicas immediately", "risk": 38, "recovery_minutes": 4, "cost_delta_pct": 42, "residual_saturation": 57, "gates": {"capacity": True, "slo": True, "failover": False, "policy": True}},
        {"id": "safe", "name": "Safe", "action": "Throttle non-critical traffic, then scale gradually", "risk": 18, "recovery_minutes": 9, "cost_delta_pct": 18, "residual_saturation": 63, "gates": {"capacity": True, "slo": True, "failover": True, "policy": True}},
        {"id": "optimal", "name": "Optimal", "action": "Rebalance cache traffic and add bounded capacity", "risk": 12, "recovery_minutes": 6, "cost_delta_pct": 23, "residual_saturation": 51, "gates": {"capacity": True, "slo": True, "failover": True, "policy": True}},
    ]
    for item in strategies:
        item["eligible"] = all(item["gates"].values())
        item["score"] = round(100 * (0.35 * (1-item["risk"]/100) + 0.25 * (1-item["residual_saturation"]/100) + 0.2 * (1-item["recovery_minutes"]/20) + 0.2 * (1-item["cost_delta_pct"]/100)), 1)
    winner = max((x for x in strategies if x["eligible"]), key=lambda x: x["score"])
    manifest = {"seed": 20260808, "network_policy": "disabled", "telemetry_hash": digest(telemetry), "configuration_hash": digest((load_multiplier, redis_capacity)), "model": "deterministic capacity projection"}
    return {
        "product": "SentinelOps Nexus",
        "title": "The Enterprise Operational Digital Twin",
        "status": "risk emerging",
        "reliability_score": max(0, round(100-saturation[3]*0.42-queues[3]*0.03)),
        "prediction": {"service": "Payment Service", "bottleneck": "Redis saturation", "time_to_impact_minutes": max(0, crossing), "confidence_label": "High" if confidence >= 80 else "Moderate", "confidence_score": confidence, "confidence_note": "Heuristic evidence score; not a calibrated probability."},
        "business_impact": {"customers_exposed": exposed_customers, "revenue_risk_inr": revenue_risk, "assumptions": {"conversion_rate": conversion_rate, "average_order_value_inr": average_order_value, "risk_window_minutes": risk_window}},
        "telemetry": telemetry,
        "evidence": evidence,
        "agents": [{"id": i, "name": n, "result": r, "evidence_ids": [e["id"] for e in evidence]} for i,n,r in AGENTS],
        "manifest": {**manifest, "manifest_hash": digest(manifest)},
        "strategies": strategies,
        "recommended_strategy": winner,
        "chaos_scenarios": [
            {"name": "Redis process crash", "baseline": "fail", "fast": "degraded", "safe": "pass", "optimal": "pass"},
            {"name": "Latency doubles", "baseline": "degraded", "fast": "degraded", "safe": "pass", "optimal": "pass"},
            {"name": "1 million-user surge", "baseline": "fail", "fast": "fail", "safe": "degraded", "optimal": "pass"},
            {"name": "Replica failover", "baseline": "fail", "fast": "fail", "safe": "pass", "optimal": "pass"},
        ],
        "approval": {"required": True, "state": "awaiting human decision", "automatic_execution": False},
        "limitations": ["Seeded deterministic demonstration", "Confidence is not a calibrated probability", "Business impact depends on displayed assumptions"],
    }
