"""Prepare Docker isolation when available, otherwise select the safe local fallback."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.tools.sandbox import docker_available  # noqa: E402


def main() -> int:
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
