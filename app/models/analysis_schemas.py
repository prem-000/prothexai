from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class AnalysisRequest(BaseModel):
    record_id: str
    # These fields can be passed if we want to avoid extra DB calls, 
    # but the task implies fetching from DB. 
    # However, strict validation on input data is requested.
    # If the user sends raw data for analysis:
    metrics: Optional[dict] = None

class AnalysisResponse(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    risk_level: str # Low, Moderate, High
    key_flags: List[str]
    recommendation_summary: List[str]
    execution_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AnalysisMetadata(BaseModel):
    user_id: str
    execution_time_ms: float
    timestamp: datetime
    record_id: str
