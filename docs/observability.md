# Observability

Integration invocations persist safe trace IDs, latency, hashes, model/prompt identifiers, token-usage slots and fallback status. The local span boundary records duration/status without secret prompts or chain-of-thought. Configure an OTLP endpoint in Cloud Run to export to Cloud Trace/Monitoring/Logging; until verified, status remains local-adapter or credentials-required.
# OpenTelemetry smoke evidence

Run `python scripts/smoke_otel.py` to prove local trace and correlation context
generation. This is `LOCAL_ADAPTER_ONLY`; it is not evidence of a Cloud Trace
export. Cloud verification requires an authenticated exported trace ID and a
matching Cloud Logging record.
