from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class OrchestrationSession:
    workflow_id: int; correlation_id: str; runtime: str; created_at: datetime=field(default_factory=lambda:datetime.now(timezone.utc)); task_ids: list[str]=field(default_factory=list)
