# Security Architecture

Human authorization uses short-lived signed role tokens and server-side RBAC. Service authorization is OIDC-ready; Cloud Run should accept Google-signed ID tokens for private service calls. Secrets belong in Secret Manager, not images or frontend bundles. Managed Google services provide their configured encryption at rest and TLS in transit; no unsupported cipher claim is made. All model/tool pathways are advisory and cannot execute production changes.
