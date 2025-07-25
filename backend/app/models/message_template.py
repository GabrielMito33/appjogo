from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class MessageType(str, enum.Enum):
    SIGNAL = "signal"           # Mensagem de sinal
    ALERT = "alert"            # Mensagem de alerta
    GALE = "gale"              # Mensagem de gale
    WIN = "win"                # Mensagem de vitória
    LOSS = "loss"              # Mensagem de loss
    WHITE = "white"            # Mensagem de branco
    RESULTS = "results"        # Mensagem de resultados/placar
    RESTART = "restart"        # Mensagem de reinício diário

class MessageTemplate(Base):
    __tablename__ = "message_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("signal_rooms.id"), nullable=True)  # Null = template global
    
    # Template Configuration
    type = Column(Enum(MessageType), nullable=False)
    name = Column(String, nullable=False)
    template = Column(Text, nullable=False)
    
    # Template Variables and Settings
    variables = Column(JSON, default={})  # Variáveis disponíveis: {cor}, {gale}, etc.
    sticker_id = Column(String)  # ID do sticker para este tipo de mensagem
    
    # Settings
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="message_templates")
    room = relationship("SignalRoom", back_populates="message_templates") 