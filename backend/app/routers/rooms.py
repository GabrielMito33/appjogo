from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.signal_room import SignalRoom
from app.schemas.signal_room import SignalRoomCreate, SignalRoomUpdate, SignalRoomResponse
from app.core.security import get_current_active_user

router = APIRouter()

@router.post("/", response_model=SignalRoomResponse)
def create_signal_room(
    room: SignalRoomCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new signal room."""
    db_room = SignalRoom(
        user_id=current_user.id,
        name=room.name,
        description=room.description,
        bot_token=room.bot_token,
        chat_id=room.chat_id,
        protection=room.protection,
        max_gales=room.max_gales,
        config=room.config
    )
    
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    
    return db_room

@router.get("/", response_model=List[SignalRoomResponse])
def read_signal_rooms(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's signal rooms."""
    rooms = db.query(SignalRoom).filter(
        SignalRoom.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return rooms

@router.get("/{room_id}", response_model=SignalRoomResponse)
def read_signal_room(
    room_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get signal room by ID."""
    room = db.query(SignalRoom).filter(
        SignalRoom.id == room_id,
        SignalRoom.user_id == current_user.id
    ).first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal room not found"
        )
    
    return room

@router.put("/{room_id}", response_model=SignalRoomResponse)
def update_signal_room(
    room_id: int,
    room_update: SignalRoomUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update signal room."""
    room = db.query(SignalRoom).filter(
        SignalRoom.id == room_id,
        SignalRoom.user_id == current_user.id
    ).first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal room not found"
        )
    
    update_data = room_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(room, field, value)
    
    db.commit()
    db.refresh(room)
    
    return room

@router.delete("/{room_id}")
def delete_signal_room(
    room_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete signal room."""
    room = db.query(SignalRoom).filter(
        SignalRoom.id == room_id,
        SignalRoom.user_id == current_user.id
    ).first()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal room not found"
        )
    
    db.delete(room)
    db.commit()
    
    return {"message": "Signal room deleted successfully"} 