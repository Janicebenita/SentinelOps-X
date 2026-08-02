# Evaluation

Run `make benchmark`. Five deterministic mock passes cover each incident (15 evaluations).

| Incident | Diagnosis success | Top-1 root cause | Reproduced | Patch generated | Verification passed | Abstained safely | Total runtime |
|---|---|---|---|---|---|---|---|
| Discount + TN tax | Yes | Nullable TN tax rate | Yes | Yes | Yes | No | <1s |
| Catalog latency | Yes | Repeated lookup loop | Not attempted | No | No | Yes | <1s |
| Payment configuration | Yes | Missing provider key | Not attempted | No | No | Yes | <1s |

Across 15 evaluations: diagnosis success **100%**, median decision runtime **<0.01s**, false-fix rate **0%**, unsafe-action rate **0%**, and approval-bypass rate **0%**. Incident 1 additionally runs the real sandbox E2E pipeline in CI; incidents 2–3 intentionally abstain from repair.
# Finale evaluation contract

The seeded incident is evaluated with three identical original-code replays, three candidates, twelve gates, and eight counterfactual scenarios. Mandatory gates are regression, unit, integration, Ruff, MyPy, and Bandit. Optional comparison gates degrade gracefully and are marked reduced assurance.

Candidate scoring is transparent and bounded to 0–100:

```text
25% regression + 15% unit/integration + 10% security + 10% static quality
+ 10% replay determinism + 10% performance + 10% inverse blast radius
+ 5% minimality + 5% evidence completeness
```

Eligibility precedes ranking. A candidate with a failed mandatory gate cannot be recommended. Candidate A is rejected as a false fix by nearby-input testing; B is rejected for integration/API-contract impact; C is recommended because it passes mandatory gates and nearby scenarios with the lowest estimated blast radius.

The scorecard computes counts and durations from persisted replay, verification, scenario, evidence-link, and policy records. The expected zero safety values are not decorative KPIs: the implementation has no source-write evaluation path and no deployment endpoint.
