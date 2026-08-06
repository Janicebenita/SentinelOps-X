from dataclasses import dataclass

@dataclass(frozen=True)
class AgentDefinition:
    name: str; description: str; instruction: str; tools: tuple[str,...]; input_schema: str; output_schema: str
    allowed_states: tuple[str,...]; timeout_seconds: int=30; max_retries: int=2
    failure_policy: str="persist failure and return control"; audit_behavior: str="append linked audit event"
    fallback_behavior: str="use deterministic backend service"

NAMES=("observer","evidence","process-discovery","prediction","digital-twin","simulation","optimization","verification","business-impact","executive")
AGENT_DEFINITIONS={name:AgentDefinition(name=name,description=f"SentinelOps {name} agent",instruction="Use only validated artifacts and backend tools; never execute production action.",tools=("get_evidence",),input_schema="A2AMessage",output_schema="AgentWorkspace",allowed_states=("CREATED","OBSERVED","PREDICTED","TWIN_READY","SIMULATED","TOURNAMENT_READY","VERIFIED","IMPACT_READY","AWAITING_HUMAN")) for name in NAMES}
