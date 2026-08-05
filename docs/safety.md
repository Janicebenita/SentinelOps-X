# Safety model

## Approver qualification

Trial Intern users cannot approve. Trial Senior Developer users require a valid signed role token and mandatory rationale. The backend—not the UI—checks role, expiry, actor, workflow state, candidate eligibility, mandatory gates, audit readiness and disabled production execution. Demonstration codes must be replaced with enterprise SSO/RBAC in production.

The Verification Agent verifies but never approves. AI models never approve. No production execution endpoint exists.

**PRODUCTION ACTION: NOT EXECUTED**

SentinelOps Nexus separates predictive reasoning from deterministic authority.

- Models and agents may propose forecasts, explanations, and interventions.
- Backend policy validates inputs, bounds scenarios, and decides eligibility.
- Failed mandatory gates override every confidence value and score.
- The Digital Twin uses a fixed seed, hashed inputs, and disabled network policy.
- Arbitrary commands, package installation, secret mounts, and protected-path changes remain prohibited.
- Business-impact assumptions are visible.
- Confidence is labelled as heuristic unless calibration is actually performed.
- Only a human can approve a proposal.
- No production execution or automatic deployment endpoint exists in the Nexus workflow.

The audit evidence supports reproducibility and tamper detection. It is not blockchain, formal proof, legal non-repudiation, or guaranteed causality.
