# Observability

Integration invocations persist safe trace IDs, latency, hashes, model/prompt identifiers, token-usage slots and fallback status. The local span boundary records duration/status without secret prompts or chain-of-thought. Configure an OTLP endpoint in Cloud Run to export to Cloud Trace/Monitoring/Logging; until verified, status remains local-adapter or credentials-required.
