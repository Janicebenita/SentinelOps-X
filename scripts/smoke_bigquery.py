"""Credentialed BigQuery write/read smoke test that emits only non-secret evidence IDs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from datetime import UTC, datetime
import hashlib

from scripts.provision_bigquery import main as provision_bigquery


def main() -> None:
    project = os.getenv("PROJECT_ID", "sentinelops-nexus-finale")
    dataset = os.getenv("BIGQUERY_DATASET", "sentinelops_nexus")
    if project != "sentinelops-nexus-finale" or shutil.which("bq") is None or shutil.which("gcloud") is None:
        raise SystemExit("Expected project and authenticated gcloud/bq CLIs are required.")
    adc = subprocess.run(  # noqa: S603
        ["gcloud", "auth", "application-default", "print-access-token"],
        text=True,
        check=False,
        capture_output=True,
    )
    if adc.returncode != 0 or not adc.stdout.strip():
        raise SystemExit("Application Default Credentials are unavailable.")
    provision_bigquery()
    event_id = f"smoke-{uuid.uuid4()}"
    query_job_id = f"sentinelops_smoke_{uuid.uuid4().hex}"
    now = datetime.now(UTC).isoformat()
    payload = {"production_action": "NOT_EXECUTED", "schema_version": "1"}
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    row = json.dumps({"event_id": event_id, "workflow_id": "cloud-smoke", "event_type": "cloud.smoke",
        "event_timestamp": now, "actor_type": "SYSTEM", "actor_id": "credentialed-smoke-test",
        "trace_id": uuid.uuid4().hex, "correlation_id": uuid.uuid4().hex,
        "payload_json": payload, "payload_hash": payload_hash, "previous_hash": "GENESIS",
        "chain_position": 1, "signature": None, "signer_key_id": None, "evidence_ids": [event_id],
        "schema_version": "1", "ingestion_timestamp": now})
    subprocess.run(  # noqa: S603
        ["bq", f"--project_id={project}", "insert", f"{dataset}.audit_event_exports", "-"],
        input=row + "\n",
        text=True,
        check=True,
    )
    query = f"SELECT event_id, payload_hash, previous_hash FROM `{project}.{dataset}.audit_event_exports` WHERE event_id='{event_id}' AND payload_hash='{payload_hash}' AND previous_hash='GENESIS' LIMIT 1"
    result = subprocess.run(  # noqa: S603
        ["bq", f"--project_id={project}", "query", "--use_legacy_sql=false", "--format=csv", f"--job_id={query_job_id}", query],
        text=True,
        check=True,
        capture_output=True,
    )
    if event_id not in result.stdout:
        raise SystemExit("BigQuery smoke row was not returned.")
    print(f"BIGQUERY_SMOKE_EVENT_ID={event_id}")
    print(f"BIGQUERY_QUERY_JOB_ID={query_job_id}")
    print(f"BIGQUERY_PAYLOAD_HASH={payload_hash}")


if __name__ == "__main__":
    main()
