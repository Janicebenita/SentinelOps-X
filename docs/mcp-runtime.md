# MCP Runtime

The tool gateway exposes the thirteen required operational tools under `/api/v1/platform/mcp`. Calls require a server-side bearer token, strict request schema, workflow lookup and correlation ID. Results come from persisted backend artifacts. The registry has no arbitrary shell or production mutation tool. Cloud gateways should replace the demo token with OIDC.
