"""Smoke-test live Cloud Run URLs without printing identity tokens or secrets."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request

SERVICES = (
    "sentinelops-frontend",
    "sentinelops-api-gateway",
    "sentinelops-orchestrator",
    "sentinelops-forecast-service",
    "sentinelops-simulation-service",
    "sentinelops-verification-service",
    "sentinelops-evidence-service",
    "sentinelops-gemma-service",
    "sentinelops-mcp-server",
)


def _gcloud(*args: str) -> str:
    result = subprocess.run(["gcloud", *args], check=True, text=True, capture_output=True)  # noqa: S603
    return result.stdout.strip()


def main() -> None:
    project = os.getenv("PROJECT_ID", "sentinelops-nexus-finale")
    region = os.getenv("REGION", "asia-south1")
    if project != "sentinelops-nexus-finale" or shutil.which("gcloud") is None:
        raise SystemExit("Expected project and authenticated gcloud CLI are required.")
    evidence: list[dict[str, str]] = []
    for service in SERVICES:
        url = _gcloud("run", "services", "describe", service, "--project", project, "--region", region, "--format=value(status.url)")
        revision = _gcloud("run", "services", "describe", service, "--project", project, "--region", region, "--format=value(status.latestReadyRevisionName)")
        headers: dict[str, str] = {}
        if service not in {"sentinelops-frontend", "sentinelops-api-gateway"}:
            token = _gcloud("auth", "print-identity-token", f"--audiences={url}")
            headers["Authorization"] = f"Bearer {token}"
        if service == "sentinelops-api-gateway":
            seed = urllib.request.Request(f"{url}/api/v1/demo/seed", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(seed, timeout=30) as response:  # noqa: S310
                if response.status not in {200, 201}:
                    raise SystemExit(f"{service} seed returned {response.status}")
        results: dict[str, str] = {}
        for endpoint in ("health", "readiness"):
            request = urllib.request.Request(f"{url}/{endpoint}", headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                if response.status != 200:
                    raise SystemExit(f"{service} {endpoint} returned {response.status}")
                body = response.read().decode("utf-8", errors="replace")
                if service == "sentinelops-api-gateway" and endpoint == "readiness" and '"ready":true' not in body.replace(" ", "").lower():
                    raise SystemExit("API readiness returned HTTP 200 but was not ready.")
                results[endpoint] = str(response.status)
        evidence.append({"service": service, "url": url, "revision": revision, **results})
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
