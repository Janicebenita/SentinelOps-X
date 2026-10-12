"""Run a reproducible SentinelOps reliability-worker example locally.

Examples:
    python scripts/domain_worker_demo.py --preset baseline
    python scripts/domain_worker_demo.py --preset surge --compact
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database import Base  # noqa: E402
from backend.app.schemas.nexus_contracts import (  # noqa: E402
    ReliabilityWorkerRequest,
    TwinControls,
)
from backend.app.services.nexus_workflow import analyze_reliability_worker  # noqa: E402


PRESETS = {
    "baseline": TwinControls(
        traffic_multiplier=1,
        redis_capacity=12000,
        application_replicas=4,
        dependency_latency_ms=20,
        source_label="demo/baseline",
    ),
    "surge": TwinControls(
        traffic_multiplier=10,
        redis_capacity=12000,
        application_replicas=4,
        dependency_latency_ms=80,
        source_label="demo/surge",
    ),
    "resilient": TwinControls(
        traffic_multiplier=2,
        redis_capacity=50000,
        application_replicas=12,
        dependency_latency_ms=10,
        source_label="demo/resilient",
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=sorted(PRESETS), default="baseline")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON")
    args = parser.parse_args()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        response = analyze_reliability_worker(
            session,
            ReliabilityWorkerRequest(
                correlation_id=f"reproducible-demo-{args.preset}",
                requested_by="local-reviewer",
                name=f"{args.preset.title()} reliability analysis",
                controls=PRESETS[args.preset],
            ),
        )
        print(response.model_dump_json(indent=None if args.compact else 2))
    finally:
        session.close()


if __name__ == "__main__":
    main()
