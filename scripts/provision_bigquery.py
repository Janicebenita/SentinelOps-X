"""Idempotently provision the SentinelOps analytical dataset through the bq CLI."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

EXPECTED_PROJECT = "sentinelops-nexus-finale"


def _run(args: list[str], *, sql: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, input=sql, text=True, check=check, capture_output=True)  # noqa: S603


def main() -> None:
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID") or ""
    dataset = os.getenv("BIGQUERY_DATASET", "sentinelops_nexus")
    region = os.getenv("GOOGLE_CLOUD_REGION") or os.getenv("REGION") or "asia-south1"
    if project != EXPECTED_PROJECT:
        raise SystemExit(f"Refusing unexpected project: {project or '<unset>'}")
    if shutil.which("bq") is None:
        raise SystemExit("bq CLI is required; no BigQuery resources were changed.")

    show = _run(["bq", f"--project_id={project}", "show", f"{project}:{dataset}"], check=False)
    if show.returncode != 0:
        _run(
            [
                "bq",
                f"--project_id={project}",
                "mk",
                "--dataset",
                f"--location={region}",
                f"{project}:{dataset}",
            ]
        )

    ddl_files = sorted(Path("sql/bigquery").glob("*.sql"))
    if len(ddl_files) != 9:
        raise SystemExit(f"Expected nine physical BigQuery DDL files; found {len(ddl_files)}.")
    for ddl_file in ddl_files:
        schema = ddl_file.read_text(encoding="utf-8")
        schema = schema.replace("${PROJECT}", project).replace("${DATASET}", dataset)
        _run(["bq", f"--project_id={project}", "query", "--use_legacy_sql=false"], sql=schema)
    print(f"BigQuery dataset and nine tables provisioned: {project}:{dataset}")


if __name__ == "__main__":
    main()
