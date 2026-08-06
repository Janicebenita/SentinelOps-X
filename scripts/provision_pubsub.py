"""Idempotently provision SentinelOps Pub/Sub topics, subscriptions and DLQs."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

EXPECTED_PROJECT = "sentinelops-nexus-finale"
TOPICS = (
    "sentinelops-agent-tasks",
    "sentinelops-scenario-events",
    "sentinelops-verification-events",
    "sentinelops-model-events",
    "sentinelops-evidence-events",
    "sentinelops-bigquery-events",
    "sentinelops-workflow-events",
)


def _run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, check=check, capture_output=True)  # noqa: S603


def main() -> None:
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID") or ""
    if project != EXPECTED_PROJECT:
        raise SystemExit(f"Refusing unexpected project: {project or '<unset>'}")
    if shutil.which("gcloud") is None:
        raise SystemExit("gcloud CLI is required; no Pub/Sub resources were changed.")

    schema_name = "sentinelops-event-envelope-v1"
    schema = _run(["gcloud", "pubsub", "schemas", "describe", schema_name, "--project", project], check=False)
    if schema.returncode != 0:
        _run(["gcloud", "pubsub", "schemas", "create", schema_name, "--project", project,
            "--type=avro", f"--definition-file={Path('schemas/pubsub/event-envelope-v1.avsc')}"])

    for topic in TOPICS:
        dlq = f"{topic}-dlq"
        subscription = f"{topic}-worker"
        for name in (topic, dlq):
            present = _run(["gcloud", "pubsub", "topics", "describe", name, "--project", project], check=False)
            if present.returncode != 0:
                args = ["gcloud", "pubsub", "topics", "create", name, "--project", project]
                if name == topic:
                    args.extend([f"--schema={schema_name}", "--message-encoding=json"])
                _run(args)
        present = _run(
            ["gcloud", "pubsub", "subscriptions", "describe", subscription, "--project", project],
            check=False,
        )
        if present.returncode != 0:
            _run(
                [
                    "gcloud",
                    "pubsub",
                    "subscriptions",
                    "create",
                    subscription,
                    "--project",
                    project,
                    "--topic",
                    topic,
                    "--dead-letter-topic",
                    dlq,
                    "--max-delivery-attempts",
                    "5",
                    "--min-retry-delay",
                    "10s",
                    "--max-retry-delay",
                    "600s",
                    "--message-retention-duration",
                    "7d",
                ]
            )
    print("Pub/Sub topics, worker subscriptions and dead-letter topics provisioned.")


if __name__ == "__main__":
    main()
