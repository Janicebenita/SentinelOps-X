from __future__ import annotations

import hashlib
import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path

database_path = Path(tempfile.gettempdir()) / "sentinelops-nexus-e2e.db"
os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402


def main() -> int:
    with TestClient(app) as client:
        reset = client.post("/api/v1/demo/reset")
        if not reset.is_success:
            raise RuntimeError(f"Reset failed: {reset.status_code} {reset.text}")
        run = client.post("/api/v1/demo/seed").json()
        run_id = run["id"]
        completed = client.post(f"/api/v1/workflows/{run_id}/run-all")
        completed.raise_for_status()
        result = completed.json()
        candidates = result["tournament_json"]["candidates"]
        fast = next(item for item in candidates if item["candidate_id"] == "fast")
        winner_id = result["tournament_json"]["recommended_candidate_id"]
        winner = next(item for item in candidates if item["candidate_id"] == winner_id)
        assert not fast["eligible"] and winner["eligible"]
        assert len(result["scenarios_json"]) == 12
        assert result["production_action_executed"] is False
        decision = client.post(
            f"/api/v1/workflows/{run_id}/approve",
            json={"actor": "e2e-human", "decision": "approve", "rationale": "All mandatory gates reviewed"},
        )
        decision.raise_for_status()
        assert decision.json()["production_action"] == "NOT EXECUTED"
        audit = client.get("/api/v1/audit/verify", params={"run_id": run_id}).json()
        assert audit["valid"] is True
        package = client.get(f"/api/v1/workflows/{run_id}/export")
        package.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
            for line in archive.read("manifest.sha256").decode().splitlines():
                expected, name = line.split("  ", 1)
                assert hashlib.sha256(archive.read(name)).hexdigest() == expected
        print({"workflow_id": run_id, "state": "DECIDED", "scenarios": 12, "fast_eligible": False, "winner": winner_id, "audit_valid": True, "production_action": "NOT EXECUTED"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
