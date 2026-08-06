# Antigravity integration boundary

Status: `DOCUMENTATION_OR_ACCESS_BLOCKED` (judge display: `BLOCKED_BY_PARTICIPANT_ACCESS`)

The repository contains a typed, read-only provider boundary and the endpoint
`GET /api/v1/integrations/antigravity/status`. The development
environment used for this release did not provide official participant
documentation, credentials, or a callable Antigravity runtime. Consequently,
SentinelOps Nexus does not claim an Antigravity invocation or substitute a
local adapter as managed-runtime evidence.

The endpoint reports whether participant access and an endpoint have been
configured. Even when configured, the status remains credential-dependent
until an authenticated smoke test records a traceable invocation. The boundary
has no workflow mutation, approval, infrastructure, or production-action
capability.

`PRODUCTION ACTION: NOT EXECUTED`
