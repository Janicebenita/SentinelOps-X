# Threat Model

## Assets and trust boundaries

Assets include workflow state, deterministic gates, evidence hashes, role verifications, audit links, exported packages and integration credentials. Trust boundaries exist at the public frontend, API gateway, human-decision endpoint, internal services, model providers, event bus and analytical exports.

## Principal threats and controls

| Threat | Control | Residual risk |
|---|---|---|
| Intern or model approves | Backend RBAC, short-lived HS256 JWT, persisted verification, state/gate revalidation | Demo codes are not enterprise identity |
| Token replay | Expiry, persisted token ID, workflow terminal state | No distributed revocation cache |
| Prompt injection changes authority | Strict schemas, evidence-only prompt, models cannot call transitions, deterministic gates authoritative | External model output still requires monitoring |
| Tool invokes infrastructure | MCP allowlist contains no shell/deploy/scale/rollback/reconfigure tool | Future connectors require review |
| Secret disclosure | Server-only configuration, redacted fingerprints, bundle/export/log tests, Secret Manager manifest references | Local `.env` and SQLite depend on host controls |
| Audit tampering | SHA-256-linked chain verification and evidence manifest | Not certified immutable storage |
| Denial of service | Request-size limit, timeout settings, per-instance rate limit | Distributed gateway limiting not deployed |
| Service impersonation | Planned Cloud Run service accounts/OIDC | IAM and OIDC not deployed or verified |
| Analytics leakage | Redaction requirement and idempotent identifiers | BigQuery writer not active |

The application has no production execution endpoint. Approval records a decision and enables evidence export only.
