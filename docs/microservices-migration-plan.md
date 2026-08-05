# Microservices Migration Plan

The repository remains a modular monolith locally and packages bounded service entrypoints for Cloud Run: frontend, API gateway, orchestrator, forecast, simulation, verification, Gemma, and evidence. Services are stateless; SQLite is local-only. Cloud workflow durability must use a managed store before production use. Pub/Sub events contain correlation, causation, retry, evidence, and trace identifiers, but consumers revalidate workflow state before acting.
