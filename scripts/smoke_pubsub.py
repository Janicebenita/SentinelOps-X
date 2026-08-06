"""Credentialed Pub/Sub publish/pull smoke test with a unique evidence ID."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
import base64


def main() -> None:
    project = os.getenv("PROJECT_ID", "sentinelops-nexus-finale")
    topic = os.getenv("PUBSUB_TOPIC", "sentinelops-workflow-events")
    subscription = f"{topic}-worker"
    if project != "sentinelops-nexus-finale" or shutil.which("gcloud") is None:
        raise SystemExit("Expected project and authenticated gcloud CLI are required.")
    event_id = f"smoke-{uuid.uuid4()}"
    correlation_id = uuid.uuid4().hex
    trace_id = uuid.uuid4().hex
    payload = json.dumps({"event_id": event_id, "schema_version": "1", "event_type": "workflow.smoke",
        "correlation_id": correlation_id, "trace_id": trace_id, "production_action": "NOT_EXECUTED"})
    publish = subprocess.run(  # noqa: S603
        ["gcloud", "pubsub", "topics", "publish", topic, "--project", project, "--message", payload, "--format=value(messageIds[0])"],
        text=True,
        check=True,
        capture_output=True,
    )
    pull = subprocess.run(  # noqa: S603
        ["gcloud", "pubsub", "subscriptions", "pull", subscription, "--project", project, "--limit", "10", "--format=json"],
        text=True,
        check=True,
        capture_output=True,
    )
    received = json.loads(pull.stdout or "[]")
    decoded: list[tuple[dict[str, object], str]] = []
    for envelope in received:
        encoded = envelope.get("message", {}).get("data", "")
        if encoded:
            decoded.append((json.loads(base64.b64decode(encoded).decode("utf-8")), envelope.get("ackId", "")))
    matching = [(item, ack_id) for item, ack_id in decoded if item.get("event_id") == event_id]
    if not matching or matching[0][0].get("schema_version") != "1" or not matching[0][1]:
        raise SystemExit("Published Pub/Sub smoke event was not consumed.")
    subprocess.run(  # noqa: S603
        ["gcloud", "pubsub", "subscriptions", "ack", subscription, "--project", project, "--ack-ids", matching[0][1]],
        text=True,
        check=True,
        capture_output=True,
    )
    print(f"PUBSUB_MESSAGE_ID={publish.stdout.strip()}")
    print(f"PUBSUB_EVENT_ID={event_id}")
    print(f"PUBSUB_TOPIC={topic}")
    print(f"PUBSUB_SUBSCRIPTION={subscription}")
    print(f"PUBSUB_CORRELATION_ID={correlation_id}")
    print(f"PUBSUB_TRACE_ID={trace_id}")


if __name__ == "__main__":
    main()
