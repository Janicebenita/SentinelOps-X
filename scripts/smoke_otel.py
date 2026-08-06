"""Verify local OpenTelemetry-compatible context propagation without cloud claims."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from backend.app.main import app


def main() -> None:
    trace_id = uuid.uuid4().hex
    correlation_id = uuid.uuid4().hex
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"X-Trace-ID": trace_id, "X-Correlation-ID": correlation_id},
        )
    if response.status_code != 200 or response.json().get("production_action") != "NOT_EXECUTED":
        raise SystemExit("Local trace-bound health probe failed.")
    print("OTEL_STATUS=LOCAL_ADAPTER_ONLY")
    print(f"OTEL_TRACE_ID={trace_id}")
    print(f"OTEL_CORRELATION_ID={correlation_id}")
    print("OTEL_CLOUD_EXPORT_VERIFIED=false")


if __name__ == "__main__":
    main()
