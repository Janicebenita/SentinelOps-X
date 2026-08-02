# API

Interactive OpenAPI is available at `http://localhost:8000/docs`.

Incident actions: create/list/get, start, collect evidence, generate hypotheses, reproduce, generate patch, verify, approve/reject, and create PR. Read endpoints expose timeline, evidence, hypotheses, patches, verification, and audit log. Demo endpoints seed, reset, generate traffic guidance, and trigger an incident.

Mutating actions enforce the state transition graph and return `409` when approval is missing for PR creation.
