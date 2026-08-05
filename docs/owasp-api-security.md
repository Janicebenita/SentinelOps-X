# OWASP API Security Checklist

- Object/workflow IDs are backend validated.
- Function authorization remains backend authoritative.
- Request size and per-instance request rates are limited.
- Strict Pydantic schemas reject excess properties.
- Sensitive integration endpoints authenticate.
- Errors avoid secrets and access codes.
- No inventory-hidden production endpoint exists.
- Outbound integrations have explicit bounded responsibilities.
- Security headers and strict CORS are configured.
- Audit and invocation metadata support investigation.

Cloud limitation: distributed rate limiting, enterprise OIDC, WAF policies and managed secret rotation require deployment credentials.
