# Prompt Engineering

Prompt assets use a CRISPE-style contract: Capacity and Role, Request, Insight and Context, Scope and Constraints, Personality and Tone, and Expected Output. Every asset includes a stable prompt ID/version, evidence inputs, refusal conditions, strict output schema, deterministic fallback and evaluation references. Prompts never contain access codes, secrets or private chain-of-thought.

Google AI Studio may be used to compare prompt versions and structured-output behavior. Promotion into the application requires the versioned repository asset, schema tests, refusal tests and a deterministic fallback. AI Studio is not a runtime dependency.
