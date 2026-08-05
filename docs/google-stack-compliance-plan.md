# Google Stack Compliance Plan

The product uses progressive activation: deterministic local behavior is always available; Google adapters activate only after explicit configuration and credential verification. Workflow authority, gates, and human authorization remain in FastAPI services. Model output is advisory.

1. Validate contracts locally for events, A2A, MCP, prompts, policy output, forecasts, and analytics rows.
2. Use Secret Manager values and dedicated service accounts in Cloud Run.
3. Activate Pub/Sub, BigQuery, Gemini/Vertex and OTLP independently and capture trace/deployment evidence.
4. Promote an integration to `IMPLEMENTED_AND_VERIFIED` only after credentialed smoke tests pass.
