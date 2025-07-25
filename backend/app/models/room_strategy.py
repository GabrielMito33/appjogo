from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class RoomStrategy(Base):
    __tablename__ = "room_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("signal_rooms.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    
    # Configuration for this specific room-strategy relationship
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # Ordem de execução nesta sala
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    room = relationship("SignalRoom", back_populates="strategies")
    strategy = relationship("Strategy", back_populates="rooms") 