# Cloud Run Deployment Plan

Prerequisites: authenticated `gcloud`, active billed project, region, enabled Run/Build/Artifact Registry/Secret Manager/Pub/Sub/BigQuery APIs, repository, service accounts and secrets. This workstation has no `gcloud`; no deployment is claimed.

Build with `gcloud builds submit --config cloudbuild.yaml --substitutions=_REGION=asia-south1`. Apply service YAML only after replacing project and image placeholders. Verify every `/health` and `/readiness`, private IAM, frontend API routing, integration calls, audit verification and evidence export. Roll back with `gcloud run services update-traffic SERVICE --to-revisions PREVIOUS=100 --region REGION`.
