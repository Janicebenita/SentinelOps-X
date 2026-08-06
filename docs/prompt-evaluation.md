# Prompt Evaluation

`prompts/evaluations` covers missing evidence, contradictions, policy failures and authority-refusal behavior. Automated provider tests prove schema validation and malformed-output rejection. A genuine model evaluation requires credentials and must record model/version, prompt version, evidence IDs, latency, output hash, trace ID and fallback state; without that evidence the integration remains credentials-required, not verified.
