$ErrorActionPreference = 'Stop'
$ProjectId = if ($env:PROJECT_ID) { $env:PROJECT_ID } else { 'sentinelops-nexus-finale' }
$Region = if ($env:REGION) { $env:REGION } else { 'asia-south1' }
if ($ProjectId -ne 'sentinelops-nexus-finale') { throw "Refusing unexpected project: $ProjectId" }
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) { throw 'gcloud is required' }
$Account = gcloud auth list --filter=status:ACTIVE --format='value(account)' | Select-Object -First 1
if (-not $Account) { throw 'No active gcloud account' }
$Billing = gcloud billing projects describe $ProjectId --format='value(billingEnabled)'
if ($Billing -ne 'True') { throw 'Billing is not enabled' }
gcloud config set project $ProjectId | Out-Null
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com bigquery.googleapis.com pubsub.googleapis.com logging.googleapis.com monitoring.googleapis.com cloudtrace.googleapis.com aiplatform.googleapis.com serviceusage.googleapis.com
gcloud artifacts repositories describe sentinelops --location $Region 2>$null
if ($LASTEXITCODE -ne 0) { gcloud artifacts repositories create sentinelops --repository-format=docker --location=$Region --description='SentinelOps Nexus service images' }
foreach ($Name in @('frontend','api-gateway','orchestrator','forecast','simulation','verification','evidence','gemma','mcp','ci-deployer')) {
  $Email = "sentinelops-$Name-sa@$ProjectId.iam.gserviceaccount.com"
  gcloud iam service-accounts describe $Email 2>$null
  if ($LASTEXITCODE -ne 0) { gcloud iam service-accounts create "sentinelops-$Name-sa" --display-name="SentinelOps $Name" }
}
$env:GOOGLE_CLOUD_PROJECT = $ProjectId
$env:GOOGLE_CLOUD_REGION = $Region
$env:BIGQUERY_DATASET = 'sentinelops_nexus'
python scripts/provision_bigquery.py
python scripts/provision_pubsub.py
foreach ($Secret in @('JWT_SIGNING_SECRET','DEMO_ROLE_CODE_HASHES','sentinelops-integration-token','sentinelops-role-token-secret','sentinelops-intern-access-code','sentinelops-senior-access-code')) {
  gcloud secrets describe $Secret --project $ProjectId 2>$null
  if ($LASTEXITCODE -ne 0) { gcloud secrets create $Secret --project $ProjectId --replication-policy=automatic | Out-Null }
}
$ApiServiceAccount = "sentinelops-api-gateway-sa@$ProjectId.iam.gserviceaccount.com"
foreach ($Secret in @('sentinelops-integration-token','sentinelops-role-token-secret','sentinelops-intern-access-code','sentinelops-senior-access-code')) {
  gcloud secrets add-iam-policy-binding $Secret --project $ProjectId --member "serviceAccount:$ApiServiceAccount" --role roles/secretmanager.secretAccessor | Out-Null
}
Write-Output "Provisioning boundary complete for project=$ProjectId region=$Region account=$Account"
Write-Output 'Secret containers exist, but no secret values were created or printed. Add versions before deployment.'
