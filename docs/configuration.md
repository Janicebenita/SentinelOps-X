# Configuration reference

Backend configuration is loaded once through the typed Pydantic `Settings` object. Unsafe production defaults fail during startup. The frontend accepts only the non-secret `API_BASE_URL` runtime value; credentials and trial-code variables are forbidden from compiled assets.

| Variable | Purpose | Required / environment | Default | Classification | Source and failure behavior |
|---|---|---|---|---|---|
| `ENVIRONMENT` | Selects local/test versus managed validation | Required in managed runtime | `development` | Non-secret | Cloud Run env; non-development enables fail-closed secret checks. |
| `PRODUCTION_EXECUTION` | Permanent execution boundary | Always | `false` | Non-secret | Any true value fails settings validation. |
| `DATABASE_URL` | Transactional workflow database | All | Local SQLite | Sensitive configuration | Cloud Run env; inaccessible path fails readiness. |
| `LLM_PROVIDER` | Provider selection | All | `mock` | Non-secret | Environment; unavailable provider activates explicit bounded fallback. |
| `AI_PROVIDER` | Compatibility alias used by deployment tooling | Optional | `mock` | Non-secret | Environment; `LLM_PROVIDER` is the backend source of truth. |
| `DEMO_REPO_PATH` | Read-only demonstration workspace | Local demo | `.` | Non-secret | Local env; invalid paths fail the relevant tool safely. |
| `DEMO_LOG_PATH` | Structured local log sink | Local demo | `data/logs/demo.jsonl` | Non-secret | Local env; parent directory must be writable. |
| `DEMO_METRICS_PATH` | Local metric sink | Local demo | `data/metrics/demo.jsonl` | Non-secret | Local env; parent directory must be writable. |
| `DEMO_TRACES_PATH` | Local trace sink | Local demo | `data/traces/demo.jsonl` | Non-secret | Local env; parent directory must be writable. |
| `DEMO_APP_URL` | Local simulator endpoint | Local demo | `http://127.0.0.1:8001` | Non-secret | Local env; unavailable simulator fails readiness. |
| `SANDBOX_IMAGE` | Fixed local replay image | Local demo | `sentinelops-sandbox:latest` | Non-secret | Local env; missing image activates documented fallback or fails the replay. |
| `MODEL_TIMEOUT_SECONDS` | Provider-call time limit | All | `30` | Non-secret | Environment; timeout produces an audited deterministic fallback. |
| `GOOGLE_CLOUD_PROJECT` | Managed service project | Google Cloud | Empty | Non-secret | Cloud Run env/ADC; cloud calls remain unverified if absent. |
| `GOOGLE_CLOUD_REGION` | Regional resource location | Google Cloud | `asia-south1` | Non-secret | Cloud Run env. |
| `GOOGLE_GENAI_USE_VERTEXAI` | Enables managed Gemini boundary | Optional | `false` | Non-secret | Environment; never changes deterministic authority. |
| `GEMINI_MODEL` | Compatibility Gemini model selector | Optional | `gemini-2.5-flash` | Non-secret | Provider env; invalid model produces safe fallback. |
| `GEMINI_API_KEY` | Optional local Gemini credential | Local adapter only | Empty | Secret | Local secret store; Google Cloud prefers ADC. |
| `GOOGLE_API_KEY` | Optional Google provider credential | Local adapter only | Empty | Secret | Local secret store; never sent to frontend. |
| `VERTEX_MODEL` | Gemini model identifier | Managed Gemini | `gemini-2.5-flash` | Non-secret | Environment; invalid model produces safe fallback. |
| `OPENAI_API_KEY` | Optional OpenAI adapter credential | Local adapter only | Empty | Secret | Local secret store; unused in deterministic mode. |
| `OPENAI_BASE_URL` | OpenAI-compatible endpoint | Optional | Official API URL | Non-secret | Local/provider env. |
| `OPENAI_MODEL` | OpenAI-compatible model selector | Optional | `gpt-4.1-mini` | Non-secret | Local/provider env. |
| `GITHUB_TOKEN` | GitHub CLI/API authentication | Developer/CI only | Empty | Secret | GitHub Actions or local credential store; never application config. |
| `GEMMA_SERVICE_URL` | Private Gemma service endpoint | Managed Gemma | Empty | Non-secret | Cloud Run env; absence uses declared local adapter. |
| `BIGQUERY_DATASET` | Analytical dataset | Google Cloud | `sentinelops_nexus` | Non-secret | Environment; BigQuery is not workflow authority. |
| `PUBSUB_TOPIC` | Default workflow event topic | Google Cloud | `sentinelops-workflow-events` | Non-secret | Environment; publish failure uses audited local fallback. |
| `CORS_ORIGINS` | Allowed browser origins | API deployment | Local Vite origins | Non-secret | Cloud Run env; unexpected origins are rejected. |
| `OIDC_ISSUER` | Expected JWT issuer | Enterprise identity | Empty locally | Non-secret | Environment; configured mismatch rejects token. |
| `OIDC_AUDIENCE` | Expected JWT audience | Enterprise identity | Empty locally | Non-secret | Environment; configured mismatch rejects token. |
| `ROLE_TOKEN_SECRET` | Signs short-lived human role tokens | Required for managed approval | Unsafe development placeholder | Secret | Secret Manager; the authorization boundary rejects use of the default outside development. |
| `ROLE_TOKEN_EXPIRY_MINUTES` | Human verification lifetime | All | `10` | Non-secret | Environment; non-positive values fail startup. |
| `INTERN_ACCESS_CODE` | Demonstration-only Intern credential | Demo only | `0000` locally | Secret | Secret Manager on Cloud Run; never persisted, logged, returned, or bundled. |
| `SENIOR_ACCESS_CODE` | Demonstration-only Senior credential | Demo only | `1111` locally | Secret | Secret Manager on Cloud Run; never persisted, logged, returned, or bundled. |
| `INTEGRATION_TOKEN` | Authenticates controlled service/MCP calls | Required for API/MCP managed runtime | Unsafe development placeholder | Secret | Secret Manager; API startup fails outside development when the default remains. |
| `RATE_LIMIT_PER_MINUTE` | Request-rate boundary | All | `120` | Non-secret | Environment; non-positive values fail startup. |
| `MAX_REQUEST_BYTES` | Request-size boundary | All | `262144` | Non-secret | Environment; non-positive values fail startup. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Trace exporter endpoint | Optional managed observability | Empty | Non-secret | Environment; empty means local propagation only. |
| `VITE_API_BASE_URL` / `API_BASE_URL` | Public frontend API origin | Frontend build/runtime | Same origin | Non-secret | Build/runtime config; missing value uses same-origin API. |
| `ANTIGRAVITY_ENDPOINT` | Read-only participant boundary | Participant access only | Empty | Non-secret | Environment; absence stays `BLOCKED_BY_PARTICIPANT_ACCESS`. |
| `ANTIGRAVITY_PARTICIPANT_ACCESS` | Confirms official participant access | Participant access only | `false` | Non-secret | Must not be enabled without evidence. |

Google Cloud deployment prefers ADC and service identity over API keys. Secret variables must never enter source, images, logs, or frontend configuration.
