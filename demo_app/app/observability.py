from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from contextvars import ContextVar
from pathlib import Path
from typing import Any

request_id_var: ContextVar[str] = ContextVar("request_id", default="unknown")
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="unknown")
START = time.perf_counter()
COUNTERS: dict[tuple[str, str, int], int] = defaultdict(int)
LATENCIES: list[dict[str, Any]] = []

def append_jsonl(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, default=str) + "\n")

def event(logger: logging.Logger, level: int, name: str, **fields: Any) -> None:
    payload = {"event": name, "request_id": request_id_var.get(), "trace_id": trace_id_var.get(), **fields}
    logger.log(level, json.dumps(payload, default=str))
    append_jsonl("data/logs/demo.jsonl", {"timestamp": time.time(), "level": logging.getLevelName(level), **payload})

class Span:
    def __init__(self, name: str, **attributes: Any) -> None:
        self.name, self.attributes, self.started = name, attributes, time.perf_counter()
    def __enter__(self) -> "Span":
        return self
    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        append_jsonl("data/traces/demo.jsonl", {"timestamp": time.time(), "trace_id": trace_id_var.get(), "span": self.name, "duration_ms": round((time.perf_counter()-self.started)*1000, 3), "status": "error" if exc else "ok", "attributes": self.attributes})

def prometheus_text() -> str:
    lines = ["# HELP http_requests_total Total HTTP requests", "# TYPE http_requests_total counter"]
    errors = total = 0
    for (method, path, status), count in COUNTERS.items():
        total += count
        errors += count if status >= 500 else 0
        lines.append(f'http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}')
    lines += ["# HELP http_error_rate Ratio of 5xx responses", "# TYPE http_error_rate gauge", f"http_error_rate {errors / total if total else 0}", "# HELP http_request_latency_ms Request latency", "# TYPE http_request_latency_ms gauge"]
    if LATENCIES:
        lines.append(f"http_request_latency_ms {LATENCIES[-1]['latency_ms']}")
    return "\n".join(lines) + "\n"

