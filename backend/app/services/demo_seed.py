from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Incident


SEEDED_INCIDENTS = (
    {
        "title": "Discount + TN tax causes checkout 500",
        "description": "SAVE10 orders in TN fail during tax arithmetic",
        "severity": "SEV1",
    },
    {
        "title": "Catalog latency regression",
        "description": "Recent commit repeats product lookup in a loop",
        "severity": "SEV2",
    },
    {
        "title": "Payment startup configuration missing",
        "description": "PAYMENT_PROVIDER_KEY is absent",
        "severity": "SEV2",
    },
)


def ensure_seeded(db: Session) -> tuple[bool, list[int]]:
    """Create deterministic demo incidents when the database is empty."""

    if db.scalar(select(Incident.id).limit(1)) is not None:
        return False, []
    rows = [Incident(**payload) for payload in SEEDED_INCIDENTS]
    db.add_all(rows)
    db.commit()
    return True, [row.id for row in rows]
