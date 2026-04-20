from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EatingRecordBase(BaseModel):
    emotion: str
    situation: str
    hunger_level: int
    is_out_of_control: bool
    notes: Optional[str] = None

class EatingRecordCreate(EatingRecordBase):
    pass

class EatingRecordUpdate(BaseModel):
    emotion: Optional[str] = None
    situation: Optional[str] = None
    hunger_level: Optional[int] = None
    is_out_of_control: Optional[bool] = None
    notes: Optional[str] = None

class EatingRecordResponse(EatingRecordBase):
    id: int
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HighRiskSituation(BaseModel):
    situation_combination: str
    count: int
    support: float
    confidence: float
    lift: float
    alternative_behaviors: list
