from importlib.util import find_spec
from ..enterprise.contracts import A2AMessage

try:
    ADK_AVAILABLE = find_spec("google.adk") is not None
except ModuleNotFoundError:
    ADK_AVAILABLE = False
def orchestrate(message: A2AMessage) -> dict:
    return {"task_id": message.task_id, "delegated_to": message.receiver,
            "runtime": "google-adk" if ADK_AVAILABLE else "local-adk-adapter",
            "state_mutation": False, "production_action": "NOT_EXECUTED"}
