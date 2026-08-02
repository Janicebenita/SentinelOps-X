$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Assert-Native([string]$Label) {
    if ($LASTEXITCODE -ne 0) { throw "$Label failed with exit code $LASTEXITCODE." }
}

$Root = Split-Path -Parent $PSScriptRoot
$Gh = 'C:\Program Files\GitHub CLI\gh.exe'
$Branch = 'finale/reliability-digital-twin'
$Tag = 'finalist-baseline-2026-08-02'

Set-Location $Root
if (-not (Test-Path $Gh)) { throw 'GitHub CLI was not found.' }
& $Gh auth status
Assert-Native 'GitHub authentication check'

if ((git branch --show-current) -eq 'main') {
    if (-not (git tag --list $Tag)) {
        git tag -a $Tag -m 'Preserve selected finalist baseline before Digital Twin extension'
    }
    if (git branch --list $Branch) { git switch $Branch } else { git switch -c $Branch }
}
if ((git branch --show-current) -ne $Branch) {
    throw "Expected branch $Branch; refusing to publish from another branch."
}

& '.\.venv\Scripts\python.exe' -m pytest backend\tests demo_app\tests -q
Assert-Native 'Backend tests'
& '.\.venv\Scripts\python.exe' -m ruff check backend demo_app scripts
Assert-Native 'Ruff'
& '.\.venv\Scripts\python.exe' -m mypy backend demo_app scripts
Assert-Native 'MyPy'
& '.\.venv\Scripts\python.exe' -m bandit -q -lll -r backend demo_app scripts
Assert-Native 'Bandit'
Push-Location frontend
try {
    pnpm test
    Assert-Native 'Frontend tests'
    pnpm run build
    Assert-Native 'Frontend build'
} finally { Pop-Location }

$Paths = @(
    '.gitignore', 'README.md', 'pyproject.toml', 'render.yaml', 'render-finale.yaml',
    'backend/app/agent/workflow.py', 'backend/app/api/routes.py',
    'backend/app/models/entities.py', 'backend/app/schemas/contracts.py',
    'backend/app/services/finale.py', 'backend/app/tools/sandbox.py',
    'backend/tests/conftest.py', 'backend/tests/test_api.py',
    'backend/tests/test_finale.py', 'docs/architecture.md', 'docs/demo-script.md',
    'docs/evaluation.md', 'docs/judge-qa.md', 'docs/limitations.md',
    'docs/safety.md', 'docs/submission-summary.md', 'frontend/src/App.test.tsx',
    'frontend/src/App.tsx', 'frontend/src/api/client.ts',
    'frontend/src/competition.css', 'frontend/src/styles.css',
    'frontend/src/types/index.ts', 'scripts/audit_live.py',
    'scripts/benchmark.py', 'scripts/generate_storytelling_video.py',
    'scripts/publish_finale.ps1', 'demo_storytelling_video.mp4',
    'demo_storytelling_video.srt'
)
git add -- $Paths
git diff --cached --check
Assert-Native 'Staged diff validation'
git commit -m 'Add Reliability Digital Twin finale experience'
Assert-Native 'Git commit'

git push origin $Tag
Assert-Native 'Baseline tag push'
git push -u origin $Branch
Assert-Native 'Finale branch push'

$Existing = & $Gh pr list --head $Branch --json url --jq '.[0].url'
if ($Existing) {
    Write-Host "Draft PR already exists: $Existing"
} else {
    $Body = @'
## What changed

- adds the Reliability Digital Twin, deterministic replay, three-candidate Repair Tournament, counterfactual simulator, blast-radius estimate, evidence graph, adversarial review and tamper-evident audit export
- strengthens human-approval and source-tree isolation guarantees
- adds the mastered narrated demo and one-click storytelling generator
- adds a separate Render finale blueprint without changing the existing finalist services

## Why

The selected SentinelOps project is extended for the finale while preserving the current `main` branch and existing Render deployment as a stable fallback.

## Validation

- backend and demo pytest suites
- frontend Vitest suite and production build
- Ruff
- MyPy
- Bandit high-severity scan
- seeded live audit including reset/repeat and tamper detection
'@
    $BodyFile = Join-Path $env:TEMP 'sentinelops-finale-pr.md'
    Set-Content -LiteralPath $BodyFile -Value $Body -Encoding utf8
    & $Gh pr create --draft --base main --head $Branch --title 'Add Reliability Digital Twin finale experience' --body-file $BodyFile
}

Write-Host 'Finalist main remains unchanged.'
Write-Host "Enhanced branch published: $Branch"
