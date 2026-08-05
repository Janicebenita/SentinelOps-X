# Approval and Trial RBAC

`POST /api/v1/auth/verify-role` securely compares server-side codes and returns an HMAC-signed, short-lived token. Tokens contain actor, role, expiry, token ID and verification record ID—never the code.

- INTERN (`0000` demo code): view, inspect, simulate, reject and request more evidence; cannot approve.
- SENIOR_DEVELOPER (`1111` demo code): may approve, reject or request more evidence with mandatory rationale.

The backend revalidates signature, expiry, actor, role, workflow state, candidate eligibility, mandatory gates, Verification Agent result, audit readiness and the non-execution boundary. Plaintext codes are not stored, logged, returned, exported or bundled into frontend production assets.

These credentials are demonstrations only. Production deployments must use enterprise identity, SSO and managed RBAC.

