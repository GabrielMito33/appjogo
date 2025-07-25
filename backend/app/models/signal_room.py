from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SignalRoom(Base):
    __tablename__ = "signal_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Telegram Bot Configuration
    bot_token = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    
    # Room Settings
    is_active = Column(Boolean, default=True)
    protection = Column(Boolean, default=True)  # Proteção no branco
    max_gales = Column(Integer, default=1)
    
    # Configuration JSON for additional settings
    config = Column(JSON, default={})
    
    # Statistics
    total_signals = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    brancos = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="signal_rooms")
    strategies = relationship("RoomStrategy", back_populates="room", cascade="all, delete-orphan")
    message_templates = relationship("MessageTemplate", back_populates="room", cascade="all, delete-orphan")
    results = relationship("ResultHistory", back_populates="room", cascade="all, delete-orphan")
    statistics = relationship("RoomStatistics", back_populates="room", cascade="all, delete-orphan") 