# Verification Agent

The Verification Agent verifies; it never approves.

Technical checks cover baseline replay, bottleneck reproduction, deterministic hashes, failover, performance, configuration policy, evidence and audit completeness, recommendation eligibility and disabled production execution. Results are persisted in `verification_records` and audited as `verification.completed`.

Approver qualification is performed through the same policy boundary: access-code validity, mapped role, permission, token expiry, workflow readiness, eligible candidate, mandatory rationale, audit readiness and disabled production execution. The result is VERIFIED, REJECTED or MORE_INFORMATION_REQUIRED.

