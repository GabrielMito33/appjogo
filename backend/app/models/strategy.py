from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class BetDirection(str, enum.Enum):
    RED = "V"      # Vermelho
    BLACK = "P"    # Preto  
    WHITE = "B"    # Branco

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Strategy Logic
    conditions = Column(JSON, nullable=False)  # Lista de condições: ["1", "P", "X"]
    bet_direction = Column(Enum(BetDirection), nullable=False)
    
    # Settings
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # Ordem de execução
    
    # Statistics
    total_signals = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="strategies")
    rooms = relationship("RoomStrategy", back_populates="strategy", cascade="all, delete-orphan")
    results = relationship("ResultHistory", back_populates="strategy") 