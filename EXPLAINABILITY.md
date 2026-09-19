# SentinelOps Nexus — Explainability

## Decision and Reasoning

SentinelOps Nexus evaluates deterministic operational evidence, specialized agent findings, simulations, and verification results before producing a recommendation. It does not autonomously execute production changes; the final decision remains with an authorized human operator.

The system separates measured facts from generated interpretation so an operator can understand how a recommendation was formed. When evidence conflicts or remains incomplete, the system surfaces that uncertainty instead of silently converting it into an autonomous action.

## Inputs and Data Sources

SentinelOps Nexus uses operational inputs such as infrastructure telemetry, service-health indicators, capacity measurements, bottleneck predictions, historical operational patterns, simulation results, intervention comparisons, verification outputs, and bounded agent findings. Deterministic telemetry and calculated system state remain authoritative when they conflict with AI-generated interpretation.

Inputs are associated with their source wherever the implementation provides that information so an operator can distinguish measured data, calculated values, simulated outcomes, and generated analysis. Missing, stale, or incomplete inputs are treated as limitations and should be exposed to the operator.

## Limits and Known Issues

SentinelOps Nexus has limitations because recommendations depend on the completeness, freshness, and quality of available operational evidence. Simulated or predicted outcomes are estimates and do not guarantee that production infrastructure will behave in exactly the same way.

The system must not autonomously execute production infrastructure changes. Recommendations may also be incomplete when telemetry is missing, agents disagree, operational context is unavailable, verification cannot be completed, or model-generated interpretation is uncertain.

## Human Review

SentinelOps Nexus is human-governed and designed to support rather than replace operational decision-making. A human operator reviews the evidence, recommendation, uncertainty, and verification state before authorizing any production action.

The explicit safety boundary is that a recommendation is not the same as an executed action. Production authorization remains outside the agent unless an authorized human-controlled process performs that action.

## Evidence and Auditability

Recommendations should be traceable to the evidence and system components that contributed to them. Where supported by the implementation, records may include timestamps, telemetry references, agent findings, simulation outputs, recommendation summaries, verification results, and human review status.

This traceability allows operators to inspect how a recommendation was produced after the fact. It also helps separate authoritative operational facts from advisory AI interpretation.
