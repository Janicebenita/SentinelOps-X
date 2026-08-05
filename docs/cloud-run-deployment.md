# Cloud Run Deployment

Use `cloudbuild.yaml` and `deploy/cloud-run/services.yaml` only after the checks in `cloud-run-deployment-plan.md`. Internal services receive no unauthenticated invoker policy. Assign one user-managed service account per service and grant only required Pub/Sub, BigQuery, Secret Manager and Run Invoker roles. Use service identity/ADC rather than shipping service-account keys. The manifests respect `PORT`, run non-root images, disable production execution and avoid baked secrets.

This repository contains deployment-ready configuration, not verified live Cloud Run evidence: `gcloud` and credentials were unavailable during this build.
