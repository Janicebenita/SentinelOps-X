from typing import Any
from sqlalchemy.orm import Session
from ..agent.state import AgentState, validate_transition
from ..models import AuditEvent, Incident
def audit(db:Session, incident_id:int, event_type:str, actor:str, inputs:dict[str,Any]|None=None, outputs:dict[str,Any]|None=None)->AuditEvent:
    event=AuditEvent(incident_id=incident_id,event_type=event_type,actor=actor,input_json=inputs or {},output_json=outputs or {}); db.add(event); db.commit(); db.refresh(event); return event
def transition(db:Session, incident:Incident, target:AgentState, actor:str="sentinelops", inputs:dict|None=None, outputs:dict|None=None)->Incident:
    current=AgentState(incident.current_state); validate_transition(current,target); incident.current_state=target.value; db.add(incident); db.add(AuditEvent(incident_id=incident.id,event_type="state_transition",actor=actor,input_json={"from":current.value,**(inputs or {})},output_json={"to":target.value,**(outputs or {})})); db.commit(); db.refresh(incident); return incident
