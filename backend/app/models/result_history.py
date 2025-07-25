from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class ResultType(str, enum.Enum):
    WIN = "win"
    LOSS = "loss"
    WHITE = "white"

class BetColor(str, enum.Enum):
    RED = "red"      # Vermelho
    BLACK = "black"  # Preto
    WHITE = "white"  # Branco

class ResultHistory(Base):
    __tablename__ = "results_history"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("signal_rooms.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    
    # Result Data
    result_type = Column(Enum(ResultType), nullable=False)
    bet_color = Column(Enum(BetColor), nullable=False)
    winning_number = Column(Integer)  # Número que saiu na Blaze
    winning_color = Column(String)    # Cor que saiu (V, P, B)
    
    # Gale Information
    gale_number = Column(Integer, default=0)  # 0 = entrada normal, 1+ = gale
    is_final_result = Column(Boolean, default=True)  # False se ainda está em sequência de gales
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    room = relationship("SignalRoom", back_populates="results")
    strategy = relationship("Strategy", back_populates="results") 