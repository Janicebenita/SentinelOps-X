from contextlib import contextmanager
from time import perf_counter
from uuid import uuid4

@contextmanager
def span(name: str, **attributes):
    """Local span boundary; configured exporters may consume the same safe fields."""
    started = perf_counter()
    record = {"name": name, "trace_id": uuid4().hex, "attributes": attributes, "started": started}
    try:
        yield record
        record["status"] = "ok"
    except Exception:
        record["status"] = "error"
        raise
    finally:
        record["duration_ms"] = int((perf_counter() - started) * 1000)
