import pytest
from backend.app.agent.state import AgentState, InvalidTransition, validate_transition

def test_valid_transition():
    validate_transition(AgentState.NEW, AgentState.ALERT_RECEIVED)

def test_invalid_transition():
    with pytest.raises(InvalidTransition):
        validate_transition(AgentState.NEW, AgentState.APPROVED)
