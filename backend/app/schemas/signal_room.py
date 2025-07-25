from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class SignalRoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    bot_token: str
    chat_id: str
    protection: bool = True
    max_gales: int = 1

class SignalRoomCreate(SignalRoomBase):
    config: Optional[Dict[str, Any]] = {}

class SignalRoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    is_active: Optional[bool] = None
    protection: Optional[bool] = None
    max_gales: Optional[int] = None
    config: Optional[Dict[str, Any]] = None

class SignalRoomResponse(SignalRoomBase):
    id: int
    user_id: int
    is_active: bool
    config: Dict[str, Any]
    total_signals: int
    wins: int
    losses: int
    brancos: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 