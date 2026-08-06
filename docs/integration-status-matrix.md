# Integration Status Matrix

The runtime source of truth is `GET /api/v1/platform/integrations`; the UI does not hardcode green states.

| Technology | Status without cloud credentials | Fallback |
|---|---|---|
| Gemini | LOCAL_ADAPTER_ONLY | deterministic evidence inventory |
| Gemma | LOCAL_ADAPTER_ONLY | deterministic consistency classifier |
| ADK | LOCAL_ADAPTER_ONLY | typed orchestrator adapter |
| A2A | IMPLEMENTED_AND_VERIFIED | SQLite persistence |
| MCP | IMPLEMENTED_AND_VERIFIED | local deterministic connectors |
| Vertex AI | ROADMAP_ONLY | authoritative bounded linear forecast |
| BigQuery | ROADMAP_ONLY | local operational database/export |
| Pub/Sub | LOCAL_ADAPTER_ONLY | idempotent in-process event bus |
| Cloud Run | IMPLEMENTED_REQUIRES_CREDENTIALS | Render/local runtime |
| Antigravity | DOCUMENTATION_UNAVAILABLE | clean no-op boundary |
| OpenTelemetry | ROADMAP_ONLY | local trace IDs/invocation records only; no exporter instrumentation verified |
