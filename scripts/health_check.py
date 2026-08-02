"""Verify that every SentinelOps demo service is accepting requests."""

from __future__ import annotations

import sys
import time

import httpx

SERVICES = {
    "frontend": "http://localhost:5173/",
    "backend": "http://localhost:8000/health",
    "demo_app": "http://localhost:8001/health",
}

STARTUP_TIMEOUT_SECONDS = 90

def main() -> int:
    pending = dict(SERVICES)
    errors = {name: "not checked" for name in SERVICES}
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    with httpx.Client(timeout=2) as client:
        while pending and time.monotonic() < deadline:
            for name, url in list(pending.items()):
                try:
                    response = client.get(url)
                    response.raise_for_status()
                    print(f"{name}: healthy ({url})")
                    del pending[name]
                except httpx.HTTPError as exc:
                    errors[name] = str(exc)
            if pending:
                time.sleep(0.5)
    if pending:
        print(
            "\n".join(f"{name}: {errors[name]}" for name in pending),
            file=sys.stderr,
        )
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
