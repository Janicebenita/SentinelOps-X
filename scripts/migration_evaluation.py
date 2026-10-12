"""Compare native and OpenAI Agents SDK reliability-worker execution.

Install the optional adapter before running:
    python -m pip install -e ".[dev,migration]"
    python scripts/migration_evaluation.py --iterations 5
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database import Base  # noqa: E402
from backend.app.migrations.openai_agents_reliability import (  # noqa: E402
    run_migrated_reliability_analysis,
)
from backend.app.schemas.nexus_contracts import (  # noqa: E402
    ReliabilityAnalysisResponse,
    ReliabilityWorkerRequest,
    TwinControls,
)
from backend.app.services.nexus_workflow import analyze_reliability_worker  # noqa: E402


CASES = {
    "baseline": TwinControls(
        traffic_multiplier=1,
        redis_capacity=12000,
        application_replicas=4,
        dependency_latency_ms=20,
        source_label="migration-evaluation/baseline",
    ),
    "surge": TwinControls(
        traffic_multiplier=10,
        redis_capacity=12000,
        application_replicas=4,
        dependency_latency_ms=80,
        source_label="migration-evaluation/surge",
    ),
    "resilient": TwinControls(
        traffic_multiplier=2,
        redis_capacity=50000,
        application_replicas=12,
        dependency_latency_ms=10,
        source_label="migration-evaluation/resilient",
    ),
}


def _new_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _time_run(
    operation: Callable[[Session, ReliabilityWorkerRequest], ReliabilityAnalysisResponse],
    request: ReliabilityWorkerRequest,
) -> tuple[ReliabilityAnalysisResponse, float]:
    session = _new_session()
    started = time.perf_counter()
    try:
        output = operation(session, request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        return output, elapsed_ms
    finally:
        session.close()


def _native(db: Session, request: ReliabilityWorkerRequest) -> ReliabilityAnalysisResponse:
    return analyze_reliability_worker(db, request)


def _migrated(db: Session, request: ReliabilityWorkerRequest) -> ReliabilityAnalysisResponse:
    return run_migrated_reliability_analysis(db, request).analysis


def _summary(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, max(0, round(0.95 * len(ordered) + 0.5) - 1))
    return {
        "median_ms": round(statistics.median(ordered), 3),
        "p95_ms": round(ordered[p95_index], 3),
        "min_ms": round(ordered[0], 3),
        "max_ms": round(ordered[-1], 3),
    }


def evaluate(iterations: int) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for case_name, controls in CASES.items():
        native_times: list[float] = []
        migrated_times: list[float] = []
        native_output: ReliabilityAnalysisResponse | None = None
        migrated_output: ReliabilityAnalysisResponse | None = None
        for index in range(iterations):
            request = ReliabilityWorkerRequest(
                correlation_id=f"migration-eval-{case_name}-{index:03d}",
                requested_by="local-migration-evaluator",
                name=f"{case_name.title()} migration evaluation",
                controls=controls,
            )
            native_output, native_ms = _time_run(_native, request)
            migrated_output, migrated_ms = _time_run(_migrated, request)
            native_times.append(native_ms)
            migrated_times.append(migrated_ms)
            if native_output.result_hash != migrated_output.result_hash:
                raise RuntimeError(f"Result hash mismatch for {case_name} iteration {index}")
        if native_output is None or migrated_output is None:
            raise RuntimeError("Evaluation produced no output")
        results[case_name] = {
            "hash_match": True,
            "result_hash": native_output.result_hash,
            "workflow_state": migrated_output.workflow_state,
            "production_action": migrated_output.approval.production_action,
            "audit_valid": migrated_output.audit_valid,
            "recommended_candidate": migrated_output.tournament.recommended_candidate_id,
            "native_latency": _summary(native_times),
            "migrated_latency": _summary(migrated_times),
        }
    return {
        "execution_mode": "offline-deterministic-tool-routing",
        "managed_model_evaluation": "NOT RUN: no provider credentials used",
        "framework": "openai-agents-sdk",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "iterations_per_case": iterations,
        "cases": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 100:
        parser.error("--iterations must be between 1 and 100")
    print(json.dumps(evaluate(args.iterations), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
