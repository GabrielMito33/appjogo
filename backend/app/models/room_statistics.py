from sqlalchemy import Column, Integer, DateTime, ForeignKey, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class RoomStatistics(Base):
    __tablename__ = "room_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("signal_rooms.id"), nullable=False)
    
    # Date for this statistic record
    date = Column(Date, nullable=False)
    
    # Daily Statistics
    total_signals = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    brancos = Column(Integer, default=0)
    
    # Calculated Metrics
    assertiveness = Column(Float, default=0.0)  # Percentual de assertividade
    max_consecutive_wins = Column(Integer, default=0)
    max_consecutive_losses = Column(Integer, default=0)
    
    # Gale Statistics
    total_gales = Column(Integer, default=0)
    gale_1_wins = Column(Integer, default=0)
    gale_2_wins = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    room = relationship("SignalRoom", back_populates="statistics") 