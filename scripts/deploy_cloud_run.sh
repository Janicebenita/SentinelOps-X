#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-sentinelops-nexus-finale}"
REGION="${REGION:-asia-south1}"
REVISION="${REVISION:-$(git rev-parse HEAD)}"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops"
[[ "$PROJECT_ID" == "sentinelops-nexus-finale" ]] || { echo "Unexpected project" >&2; exit 2; }

for secret in sentinelops-integration-token sentinelops-role-token-secret sentinelops-intern-access-code sentinelops-senior-access-code; do
  gcloud secrets versions access latest --secret "$secret" --project "$PROJECT_ID" >/dev/null
done

deploy_private() {
  local service="$1" image="$2" account="$3" secret_args="${4:-}" image_revision="${5:-$REVISION}"
  local extra=()
  if [[ -n "$secret_args" ]]; then extra=(--set-secrets "$secret_args"); fi
  gcloud run deploy "$service" --project "$PROJECT_ID" --region "$REGION" --platform managed \
    --image "${REGISTRY}/${image}:${image_revision}" --service-account "${account}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --no-allow-unauthenticated --port 8080 --cpu 1 --memory 512Mi --concurrency 20 --timeout 60 \
    --min-instances 0 --max-instances 5 --set-env-vars PRODUCTION_EXECUTION=false,ENVIRONMENT=production \
    "${extra[@]}"
}

deploy_private sentinelops-orchestrator orchestrator sentinelops-orchestrator-sa
deploy_private sentinelops-forecast-service forecast sentinelops-forecast-sa
deploy_private sentinelops-simulation-service simulator sentinelops-simulation-sa
deploy_private sentinelops-verification-service verification sentinelops-verification-sa
deploy_private sentinelops-evidence-service evidence sentinelops-evidence-sa
deploy_private sentinelops-gemma-service gemma sentinelops-gemma-sa
deploy_private sentinelops-mcp-server mcp sentinelops-mcp-sa "INTEGRATION_TOKEN=sentinelops-integration-token:latest,ROLE_TOKEN_SECRET=sentinelops-role-token-secret:latest" "${MCP_REVISION:-$REVISION}"

API_SA="sentinelops-api-gateway-sa@${PROJECT_ID}.iam.gserviceaccount.com"
ORCHESTRATOR_SA="sentinelops-orchestrator-sa@${PROJECT_ID}.iam.gserviceaccount.com"
for service in sentinelops-forecast-service sentinelops-simulation-service sentinelops-verification-service sentinelops-evidence-service sentinelops-gemma-service sentinelops-mcp-server; do
  gcloud run services add-iam-policy-binding "$service" --project "$PROJECT_ID" --region "$REGION" --member "serviceAccount:${API_SA}" --role roles/run.invoker >/dev/null
  gcloud run services add-iam-policy-binding "$service" --project "$PROJECT_ID" --region "$REGION" --member "serviceAccount:${ORCHESTRATOR_SA}" --role roles/run.invoker >/dev/null
done

gcloud run deploy sentinelops-api-gateway --project "$PROJECT_ID" --region "$REGION" --platform managed \
  --image "${REGISTRY}/api:${REVISION}" --service-account "$API_SA" --allow-unauthenticated \
  --port 8080 --cpu 1 --memory 512Mi --concurrency 40 --timeout 60 --min-instances 0 --max-instances 5 \
  --set-env-vars PRODUCTION_EXECUTION=false,ENVIRONMENT=production,DEMO_APP_URL=,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION},BIGQUERY_DATASET=sentinelops_nexus,PUBSUB_TOPIC=sentinelops-workflow-events \
  --set-secrets INTEGRATION_TOKEN=sentinelops-integration-token:latest,ROLE_TOKEN_SECRET=sentinelops-role-token-secret:latest,INTERN_ACCESS_CODE=sentinelops-intern-access-code:latest,SENIOR_ACCESS_CODE=sentinelops-senior-access-code:latest

API_URL="$(gcloud run services describe sentinelops-api-gateway --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
[[ "$API_URL" == https://* ]] || { echo "API gateway URL unavailable" >&2; exit 6; }

gcloud run deploy sentinelops-frontend --project "$PROJECT_ID" --region "$REGION" --platform managed \
  --image "${REGISTRY}/frontend:${REVISION}" --service-account "sentinelops-frontend-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --allow-unauthenticated --port 8080 --cpu 1 --memory 256Mi --concurrency 80 --timeout 60 --min-instances 0 --max-instances 5 \
  --set-env-vars "API_BASE_URL=${API_URL}"

FRONTEND_URL="$(gcloud run services describe sentinelops-frontend --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
[[ "$FRONTEND_URL" == https://* ]] || { echo "Frontend URL unavailable" >&2; exit 7; }
gcloud run services update sentinelops-api-gateway --project "$PROJECT_ID" --region "$REGION" \
  --update-env-vars "CORS_ORIGINS=${FRONTEND_URL}" >/dev/null

echo "FRONTEND_URL=${FRONTEND_URL}"
echo "API_URL=${API_URL}"
echo "Cloud Run deployment submitted for revision ${REVISION}. Run scripts/smoke_cloud_run.py before recording success."
