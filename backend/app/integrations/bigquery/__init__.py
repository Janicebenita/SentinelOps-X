from typing import Any
def insert_id(kind: str, record: dict[str, Any]) -> str:
    from ...enterprise.runtime import digest
    return digest({"kind": kind, "record": record})
