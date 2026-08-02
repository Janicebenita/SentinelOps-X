# Safety model

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
