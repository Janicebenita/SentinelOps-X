# SentinelOps Nexus Upgrade Plan

1. Add append-only execution, role-verification, human-decision and verification-record tables using SQLAlchemy `create_all` compatibility and startup indexes.
2. Add HMAC-signed, short-lived role tokens; server-only access-code comparison and fingerprints; strict typed error responses.
3. Add a workforce registry and real agent execution service that validates state, invokes or validates workflow services, persists execution records and appends chained audit events.
4. Extend the Verification Agent for technical and approver-qualification checks without decision authority.
5. Replace fixed approval calls with actor/code verification, backend token enforcement, mandatory rationale and three human decisions.
6. Add a fast landing route and lazy command-centre, workforce, agent, workflow, verification, approval, evidence, audit, export, architecture, safety and docs routes.
7. Defer non-critical queries, set query freshness, lazy-load Recharts and reduce the initial bundle/request count.
8. Separate lightweight health from readiness; move schema/bootstrap work to application lifespan; avoid demo seeding on the critical health path.
9. Expand backend, frontend and E2E tests; add credential leakage and non-execution assertions to CI.
10. Update environment examples, Render, Docker, README, architecture, security, deployment and final validation documents.
11. Run the complete validation matrix, push GitHub main, redeploy existing Render Blueprint services and verify live behavior.

