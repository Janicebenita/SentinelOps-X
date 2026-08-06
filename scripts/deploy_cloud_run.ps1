$ErrorActionPreference = 'Stop'
$ProjectId = if ($env:PROJECT_ID) { $env:PROJECT_ID } else { 'sentinelops-nexus-finale' }
$Region = if ($env:REGION) { $env:REGION } else { 'asia-south1' }
$Revision = if ($env:REVISION) { $env:REVISION } else { (git rev-parse HEAD) }
if ($ProjectId -ne 'sentinelops-nexus-finale') { throw "Unexpected project: $ProjectId" }
& bash scripts/deploy_cloud_run.sh
