"""Start the complete local/Codespaces demo and supervise all services."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from health_check import main as health_check

ROOT = Path(__file__).parents[1]

def main() -> int:
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if npm is None:
        print("npm is required", file=sys.stderr)
        return 1
    env = {**os.environ, "LLM_PROVIDER": "mock"}
    commands = [
        ([sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"], ROOT),
        ([sys.executable, "-m", "uvicorn", "demo_app.app.main:app", "--host", "0.0.0.0", "--port", "8001"], ROOT),
        ([npm, "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"], ROOT / "frontend"),
    ]
    processes = [subprocess.Popen(command, cwd=cwd, env=env) for command, cwd in commands]
    try:
        time.sleep(1)
        if health_check() != 0:
            return 1
        print("SentinelOps is ready: dashboard 5173, API 8000, demo app 8001")
        while all(process.poll() is None for process in processes):
            time.sleep(1)
        return next((process.returncode or 1 for process in processes if process.poll() is not None), 1)
    except KeyboardInterrupt:
        return 0
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill()

if __name__ == "__main__":
    raise SystemExit(main())
