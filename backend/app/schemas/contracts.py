from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
class IncidentCreate(BaseModel):
    title:str; description:str=""; severity:str="SEV2"; source:str="demo"; service_name:str="sentinel-shop"
class IncidentRead(IncidentCreate):
    model_config=ConfigDict(from_attributes=True); id:int; status:str; current_state:str; created_at:datetime; updated_at:datetime
class HypothesisDecision(BaseModel):
    title:str; explanation:str; evidence_for:list[str]=Field(min_length=1); evidence_against:list[str]; confidence:float=Field(ge=0,le=1); relevant_files:list[str]
class HypothesisResponse(BaseModel): hypotheses:list[HypothesisDecision]=Field(min_length=2,max_length=3)
class PatchProposal(BaseModel):
    summary:str; target_files:list[str]=Field(min_length=1,max_length=5); patch:str; expected_effect:str; risks:list[str]; verification_plan:list[str]
class ApprovalInput(BaseModel): approved_by:str=Field(min_length=2,max_length=100)
class ReplayInput(BaseModel):
    candidate_id:str|None=None; attempts:int=Field(default=3,ge=3,le=10)
class CounterfactualInput(BaseModel):
    shipping_region:str=Field(default="TN",min_length=2,max_length=3)
    discount_code:str|None="SAVE10"; tax_rate:float|None=None
    discount_percentage:float=Field(default=10,ge=0,le=100); cart_value:float=Field(default=48,ge=0,le=1_000_000)
    dependency_latency_ms:int=Field(default=40,ge=0,le=60_000); database_available:bool=True
    retry_count:int=Field(default=1,ge=0,le=10); feature_flag:bool=True
    traffic_volume:int=Field(default=1,ge=1,le=100_000); concurrent_requests:int=Field(default=1,ge=1,le=10_000)
