# Google Stack Compliance Matrix

Validation date: 2026-08-06. “Deployed” means authenticated cloud deployment evidence, not a YAML file.

| Technology | Required | Implemented | Tested | Deployed | Credentials Required | Fallback | Evidence | Final Status |
|---|---:|---:|---:|---:|---:|---|---|---|
| Google AI Studio | Yes | prompt workflow | fixtures | No | No | versioned prompts | `prompts/`, AI Studio doc | LOCAL_ADAPTER_ONLY |
| Gemini | Yes | schema/advisory provider boundary | Yes | No | Yes | evidence inventory | runtime + model tests | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Gemma | Yes | policy/evidence service routes | Yes | No | Yes for model | deterministic classifier | Gemma tests/docs | LOCAL_ADAPTER_ONLY |
| Antigravity | conditional | adapter assessment only | search verified | No | Unknown | none invented | assessment | DOCUMENTATION_UNAVAILABLE |
| Google ADK | Yes | typed orchestration boundary | local boundary | No | Yes | local orchestrator | `backend/app/adk` | LOCAL_ADAPTER_ONLY |
| A2A | Yes | typed persisted messages | Yes | No | No | SQLite | contract test | IMPLEMENTED_AND_VERIFIED |
| MCP | Yes | 13 authenticated tools | Yes | No | No | deterministic connectors | MCP API tests | IMPLEMENTED_AND_VERIFIED |
| Vertex AI | Yes | supplemental forecast contract | fallback tested | No | Yes | bounded linear model | forecast test | IMPLEMENTED_REQUIRES_CREDENTIALS |
| BigQuery | Yes | schemas/idempotency boundary | local schema test | No | Yes | SQLite/export | SQL + docs | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Pub/Sub | Yes | envelope/idempotency/DLQ boundary | Yes | No | Yes | local event bus | event test | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Cloud Run | Yes | eight service manifests/images | config only | No | Yes | Render/local | deploy files | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Secret Manager | Yes | deployment design/env boundary | config review | No | Yes | local env | security docs | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Artifact Registry | Yes | Cloud Build image targets | config review | No | Yes | local Docker | cloudbuild | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Cloud Logging/Monitoring/Trace | Yes | structured trace boundary | local trace tested | No | Yes | invocation DB | observability docs | IMPLEMENTED_REQUIRES_CREDENTIALS |
| OpenTelemetry | Yes | safe local span contract | type/security checks | No | endpoint | trace IDs | observability module | LOCAL_ADAPTER_ONLY |
| OAuth2/OIDC | Yes | service-identity-ready configuration | config review | No | issuer/IAM | signed demo JWT-style tokens | security docs | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Rate limiting / OWASP controls | Yes | active middleware | Yes | Render pending | No | per-instance bucket | security test | IMPLEMENTED_AND_VERIFIED |

The deterministic workflow, gate authority, Intern block, Senior rationale requirement, audit chain, evidence export and `PRODUCTION ACTION: NOT EXECUTED` remain implemented and verified by the full suite.
