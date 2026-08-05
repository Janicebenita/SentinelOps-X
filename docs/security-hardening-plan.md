# Security Hardening Plan

Implemented locally: backend RBAC, signed short-lived role tokens, request-size limits, per-instance rate limiting, strict schemas, narrow CORS, security headers, authenticated integration APIs, idempotency, redacted code fingerprints, and no production mutation tools.

Cloud activation: OIDC ID tokens for private Cloud Run service calls, user-managed service accounts with `roles/run.invoker`, Secret Manager, managed TLS, and centralized rate limiting at an API gateway. Demo access codes must be replaced by enterprise identity.
