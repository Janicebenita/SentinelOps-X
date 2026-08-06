# Judge Compliance Matrix

Evidence date: 2026-08-06. A deployment claim requires a reachable service and authenticated evidence; files alone do not qualify.

| Judge requirement | Current state | Implementation | Source files | Tests | Deployment evidence | Credentials required | Limitations | Final status |
|---|---|---|---|---|---|---:|---|---|
| Google AI Studio | Versioned prompt workflow | CRISPE prompt/evaluation assets | `prompts/`, prompt docs | prompt contract test | Not runtime applicable | No | Studio session history not exported | LOCAL_ADAPTER_ONLY |
| Gemini | Core reasoning call path and fallback | Strict evidence output, audit metadata | `providers/gemini`, `enterprise/runtime.py` | provider/schema/authority tests | Render reports mock | Yes | No genuine model call captured | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Gemma | Remote/private path plus fallback | Exact policy/evidence endpoints | `services/gemma`, `providers/gemma` | fallback/authority tests | None | Yes | No model endpoint deployed | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Google ADK | Active local orchestration adapter | Ten registered agent definitions, session/runtime boundary | `backend/app/adk` | registry/runtime/A2A test | None | Yes | Official ADK unavailable | LOCAL_ADAPTER_ONLY |
| A2A | Active typed communication | Delegation/completion, persistence, shared trace | `a2a`, `workforce.py`, models | schema/idempotency/trace tests | Feature branch not deployed | No | Local SQL persistence | IMPLEMENTED_AND_VERIFIED |
| MCP | Active authenticated gateway | 13 read-only tools | `mcp`, enterprise router | contract/auth/no-mutation tests | Feature branch not deployed | No | Not official SDK transport | IMPLEMENTED_AND_VERIFIED |
| Vertex AI | Response contract only | Deterministic fallback envelope | `integrations/vertex_ai` | fallback test | None | Yes | No Vertex client | ROADMAP_ONLY |
| BigQuery | Schemas/helper only | Nine partitioned/clustered schemas | `integrations/bigquery`, `sql/` | static/local tests | None | Yes | No writer or row ID evidence | ROADMAP_ONLY |
| Pub/Sub | Local idempotent event bus | Required event envelope/DLQ boundary | enterprise contracts/runtime | delivery/idempotency test | None | Yes | No Google publisher/subscription | LOCAL_ADAPTER_ONLY |
| Cloud Run | Build/manifests | Eight service images/manifests | Dockerfiles, `deploy/cloud-run` | CI Docker builds | No `run.app` URL | Yes | No gcloud/project/IAM | IMPLEMENTED_REQUIRES_CREDENTIALS |
| OAuth2/JWT | JWT active, OIDC absent | Three-segment HS256 short-lived role JWT | `auth/roles.py` | invalid/expired/role tests | Render role tests | OIDC yes | Demo identity only | LOCAL_ADAPTER_ONLY |
| Rate limiting | Active | HTTP 429 and request-size middleware | `security.py` | enforcement test | Not re-probed on branch | No | Per-instance | IMPLEMENTED_AND_VERIFIED |
| OWASP protections | Active local controls | RBAC, schemas, limits, headers, safe errors | security/auth/API | security suite/Bandit | Partial Render | No | WAF/distributed controls absent | IMPLEMENTED_AND_VERIFIED |
| Encryption at rest | Documented accurately | Managed-service plan; SQLite limitation | security docs | consistency review | No Google resources | Yes | No cloud configuration to inspect | IMPLEMENTED_REQUIRES_CREDENTIALS |
| OpenTelemetry | Local trace helper only | Trace/correlation IDs | observability/runtime | trace propagation test | No exported trace | Yes | No SDK/exporter instrumentation | ROADMAP_ONLY |
| Microservices | Independently packaged boundaries | Eight non-root service images | `services/`, Dockerfiles | CI builds/health | Not Cloud Run deployed | Yes | Some services remain thin façades | IMPLEMENTED_REQUIRES_CREDENTIALS |
| Async communication | Local bus/A2A active | typed envelope, idempotency, retry/DLQ fields | enterprise runtime/contracts | event tests | No Pub/Sub evidence | Yes | In-process bus | LOCAL_ADAPTER_ONLY |
| Antigravity | No documented interface | Clean assessment/no fabricated API | assessment doc | repository/package/env search | None | Unknown | Official participant docs missing | DOCUMENTATION_UNAVAILABLE |

All rows preserve deterministic authority, human approval, audit-chain verification, evidence export and `PRODUCTION ACTION: NOT EXECUTED`.
