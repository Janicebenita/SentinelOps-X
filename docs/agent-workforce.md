# AI Workforce

SentinelOps Nexus exposes eleven clickable, backend-connected workspaces: Nexus Orchestrator, Observer, Evidence, Process Discovery, Prediction, Digital Twin, Simulation, Optimization, Verification, Business Impact and Executive.

Each workspace presents purpose, responsibilities, status, workflow ID, duration, inputs, outputs, evidence, assumptions, errors, retry count and result hash. Run and rerun actions call FastAPI, validate state, persist `AgentExecution`, append chained audit events and refresh the UI. When a stage has already completed, rerun validates the persisted artifact rather than fabricating a new frontend result.

Only structured reasoning summaries, evidence references, assumptions, decisions and outputs are shown. Hidden chain-of-thought is never exposed.

