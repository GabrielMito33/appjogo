from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.strategy import BetDirection

class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    conditions: List[str]  # Lista como ["1", "P", "X"]
    bet_direction: BetDirection
    priority: int = 1

class StrategyCreate(StrategyBase):
    pass

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[List[str]] = None
    bet_direction: Optional[BetDirection] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None

class StrategyResponse(StrategyBase):
    id: int
    user_id: int
    is_active: bool
    total_signals: int
    wins: int
    losses: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 