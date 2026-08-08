from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BusinessAssumptions(StrictModel):
    conversion_rate: float = Field(0.034, ge=0, le=1)
    average_order_value_inr: float = Field(3200, gt=0)
    risk_window_minutes: int = Field(60, ge=1, le=1440)
    projected_failure_rate: float = Field(0.18, ge=0, le=1)
    sla_penalty_inr: float = Field(250000, ge=0)


class TwinControls(StrictModel):
    traffic_multiplier: float = Field(1, ge=0.5, le=10)
    redis_capacity: int = Field(12000, ge=6000, le=50000)
    application_replicas: int = Field(4, ge=1, le=50)
    dependency_latency_ms: int = Field(20, ge=0, le=5000)
    failover_state: Literal["primary", "replica", "unavailable"] = "primary"
    seed: int = 20260808
    source_label: str = Field("seeded/payment-service", min_length=3, max_length=200)
    normalization_notes: list[str] = Field(default_factory=list, max_length=50)
    telemetry_points: list["TelemetryPoint"] = Field(default_factory=list, max_length=1000)
    business: BusinessAssumptions = Field(default_factory=lambda: BusinessAssumptions(
        conversion_rate=0.034,
        average_order_value_inr=3200,
        risk_window_minutes=60,
        projected_failure_rate=0.18,
        sla_penalty_inr=250000,
    ))


class EvidenceUpload(StrictModel):
    filename: str = Field(min_length=1, max_length=160)
    category: Literal["telemetry", "configuration", "topology", "slo", "other"] = "configuration"
    content: str = Field(min_length=2, max_length=10485760)


class OperationalJsonImport(StrictModel):
    filename: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=2, max_length=10485760)


class TelemetryPoint(StrictModel):
    label: str
    minute: int
    request_rate: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    redis_cpu_pct: float
    redis_memory_pct: float
    cache_hit_rate_pct: float
    queue_depth: int
    application_replicas: int
    error_rate_pct: float
    order_conversion_rate: float
    average_order_value_inr: float
    reactive_alert: bool


TwinControls.model_rebuild()


class EvidenceRecord(StrictModel):
    evidence_id: str
    category: str
    source: str
    observed_at: datetime
    payload: dict[str, Any]
    summary: str
    content_hash: str


class ForecastResult(StrictModel):
    model_name: str
    equation: str
    observation_window: str
    forecast_horizon_minutes: int
    safe_threshold_pct: float
    reactive_alert_threshold_pct: float
    predicted_crossing_minutes: int
    predicted_customer_impact_minutes: int
    residual_mae: float
    error_bound_minutes: int
    heuristic_evidence_score: int = Field(ge=0, le=100)
    confidence_label: Literal["Low", "Moderate", "High"]
    assumptions: list[str]
    evidence_ids: list[str]


class TopologyResult(StrictModel):
    nodes: list[dict[str, str]]
    edges: list[dict[str, str]]
    critical_path: list[str]
    constraint: str
    evidence_ids: list[str]


class TwinManifestContract(StrictModel):
    twin_id: str
    created_at: datetime
    source_revision: str
    service_topology_hash: str
    telemetry_window_hash: str
    configuration_hash: str
    dependency_fingerprint: str
    forecasting_parameters: dict[str, Any]
    random_seed: int
    capacity_constraints: dict[str, Any]
    slo_definitions: dict[str, Any]
    business_assumptions: BusinessAssumptions
    network_policy: Literal["disabled"]
    allowed_scenarios: list[str]
    resource_limits: dict[str, Any]
    evidence_references: list[str]
    manifest_hash: str
    limitation: str


class ScenarioResultContract(StrictModel):
    scenario_id: str
    name: str
    inputs: dict[str, Any]
    status: Literal["pass", "degraded", "fail"]
    bottleneck_avoided: bool
    p95_ms: float
    error_rate_pct: float
    recovery_minutes: int
    result_hash: str
    evidence_ids: list[str]


class GateResult(StrictModel):
    gate: str
    mandatory: bool = True
    passed: bool
    details: str
    evidence_ids: list[str]


class InterventionCandidate(StrictModel):
    candidate_id: Literal["fast", "safe", "optimal"]
    name: str
    action: str
    expected_benefit: str
    cost_estimate_inr: int
    risk_score: int = Field(ge=0, le=100)
    recovery_minutes: int
    reversible: bool
    assumptions: list[str]
    gates: list[GateResult]
    score_components: dict[str, float]
    score: float = Field(ge=0, le=100)
    eligible: bool
    verdict: str


class TournamentResult(StrictModel):
    candidates: list[InterventionCandidate]
    recommended_candidate_id: str
    weights: dict[str, float]
    rule: str
    twin_id: str


class BusinessImpactResult(StrictModel):
    customers_at_risk: int
    orders_at_risk: int
    revenue_exposure_inr: float
    sla_breach_risk_label: str
    estimated_recovery_minutes: int
    intervention_cost_estimate_inr: int
    formula: str
    inputs: dict[str, float]
    disclaimer: str
    evidence_ids: list[str]


class ExecutiveBrief(StrictModel):
    summary: str
    recommendation: str
    uncertainty: list[str]
    contradictory_evidence: list[str]
    evidence_ids: list[str]
    production_action: Literal["NOT EXECUTED"] = "NOT EXECUTED"


class AgentEnvelope(StrictModel):
    agent_id: str
    agent_name: str
    run_id: int
    input_hash: str
    output_type: str
    output: dict[str, Any]
    evidence_ids: list[str]
    created_at: datetime


class HumanDecisionInput(StrictModel):
    actor: str = Field(min_length=2, max_length=100)
    decision: Literal["approve", "reject", "request_more_evidence"]
    rationale: str = Field(min_length=3, max_length=1000)


class RunCreate(StrictModel):
    name: str = Field("Payment Service capacity forecast", min_length=3, max_length=160)
    controls: TwinControls = Field(default_factory=lambda: TwinControls(
        traffic_multiplier=1,
        redis_capacity=12000,
        application_replicas=4,
        dependency_latency_ms=20,
        failover_state="primary",
        seed=20260808,
        source_label="seeded/payment-service",
    ))
