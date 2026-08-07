# CI/CD controls

## Pull-request and branch validation

`.github/workflows/validate.yml` runs on pull requests to `main`, pushes to `main` and `feat/google-native-enterprise-compliance`, and manual dispatch. Independent jobs expose the failing boundary clearly:

1. Python tests, coverage, Ruff, MyPy, and Bandit.
2. Frontend type checking, component/integration coverage, and production build.
3. Gitleaks, dependency audits, compiled-bundle scanning, and forbidden-route proof.
4. Gemini/Gemma, prompt, ADK, A2A, MCP, Antigravity, and cloud contract tests.
5. Nine independently deployable container builds.
6. A deterministic end-to-end governed workflow.

Coverage, security summaries, and E2E summaries are uploaded as non-secret artifacts.

## Google Cloud runtime workflow

`.github/workflows/google-cloud-runtime.yml` is manual and protected by the `google-cloud-demo` environment. It uses GitHub OIDC and Workload Identity Federation (`id-token: write`) rather than a service-account JSON key. Deployment is optional; existing resources can be verified read-only. When explicitly selected, authenticated smoke tests record non-secret Cloud Run revisions, BigQuery evidence IDs, Pub/Sub message IDs, Cloud Logging output, and local OpenTelemetry propagation.

Deployment does not mean production mutation by the product. CI may deploy reviewed SentinelOps application revisions; the running product still enforces `PRODUCTION ACTION: NOT EXECUTED`.

## Rollback

Cloud Run rollback routes traffic to a previously verified revision. Secret changes require a new Cloud Run revision; rollback never exposes secret values or grants the application infrastructure-mutation authority.
