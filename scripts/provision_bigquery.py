"""Prints the credentialed BigQuery provisioning command; does not fabricate a deployment."""
from backend.app.config import settings

def main() -> None:
    if not settings.google_cloud_project:
        raise SystemExit("GOOGLE_CLOUD_PROJECT is required; no resources were changed.")
    print(f"bq query --use_legacy_sql=false --parameter=PROJECT::{settings.google_cloud_project} --parameter=DATASET::{settings.bigquery_dataset} < sql/bigquery_schemas.sql")

if __name__ == "__main__": main()
