"""Prepare Docker isolation when available, otherwise select the safe local fallback."""

from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.tools.sandbox import docker_available  # noqa: E402


def main() -> int:
    if os.environ.get("SENTINELOPS_SKIP_SANDBOX_BUILD") == "1":
        print("Sandbox image build skipped for service health validation.")
        return 0
    if not docker_available():
        print("Docker not found; SentinelOps will use the restricted Local Sandbox.")
        return 0
    print("Docker found; building the restricted SentinelOps sandbox image.")
    result = subprocess.run(
        ["docker", "build", "-t", "sentinelops-sandbox:latest", "-f", "sandbox/Dockerfile", "."],
        cwd=ROOT,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
