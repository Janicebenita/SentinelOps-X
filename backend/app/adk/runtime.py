from importlib.util import find_spec
from ..enterprise.contracts import A2AMessage
from .agents import AGENT_DEFINITIONS

try: ADK_AVAILABLE=find_spec("google.adk") is not None
except ModuleNotFoundError: ADK_AVAILABLE=False

def orchestrate(message:A2AMessage)->dict:
    agent_name=message.receiver.removesuffix("-agent")
    definition=AGENT_DEFINITIONS.get(agent_name)
    return {"task_id":message.task_id,"delegated_to":message.receiver,"registered":definition is not None,
        "runtime":"google-adk" if ADK_AVAILABLE else "local-adk-adapter","tools":list(definition.tools) if definition else [],
        "state_mutation":False,"production_action":"NOT_EXECUTED"}
