# Security Architecture

Human authorization uses short-lived signed role tokens and server-side RBAC. Service authorization is OIDC-ready; Cloud Run should accept Google-signed ID tokens for private service calls. Secrets belong in Secret Manager, not images or frontend bundles. Managed Google services provide their configured encryption at rest and TLS in transit; no unsupported cipher claim is made. All model/tool pathways are advisory and cannot execute production changes.

## Configuration and secret controls

The backend uses one typed Pydantic settings boundary. `PRODUCTION_EXECUTION=true` and non-positive request limits fail during startup. Services validate only the secrets they consume: the API rejects the development integration token outside development, while the role boundary rejects its development signing secret when authorization is invoked. This preserves fail-closed behavior without forcing unrelated forecast or simulation services to receive unused secrets. Role tokens validate signature, expiration, persisted token ID, actor, role, and configured issuer/audience. Access codes are compared server-side and only a redacted HMAC fingerprint is persisted.

Cloud Run receives secrets through Secret Manager references and dedicated service accounts with minimum `secretAccessor` grants. GitHub deployment uses short-lived OIDC federation; no service-account JSON key is required. The frontend runtime config contains only the public API origin, and CI scans built assets for server-only names, private-key material, service-account JSON, and token patterns.

## Rotation readiness

1. Add a new enabled Secret Manager version without printing its value.
2. Deploy a new Cloud Run revision referencing `latest`, or deliberately pin the approved version when change control requires reproducibility.
3. Run readiness, authorization, and evidence-export smoke tests before shifting all traffic.
4. Roll back traffic to the prior healthy revision if validation fails; disable the new secret version after rollback analysis.
5. Remove old versions only after the rollback window closes.

A running container is not assumed to reload a rotated secret automatically. Rotation becomes effective through a reviewed Cloud Run revision update. Service accounts retain least-privilege access throughout.
