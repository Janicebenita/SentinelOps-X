# Gemma Policy Service

The private service contract exposes `POST /v1/policy/review`, `POST /v1/evidence/check`, `GET /health` and `GET /readiness`. A configured remote provider is called with a bounded timeout. Responses attempting gate override or approval authority are rejected and replaced with the deterministic fallback. No deployed Gemma model is currently verified, so the final status remains `IMPLEMENTED_REQUIRES_CREDENTIALS`.
