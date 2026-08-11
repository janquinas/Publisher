"""
Modelo de Plataforma do Banco de Dados
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from core.database.config import Base


class PlatformDB(Base):
    """Modelo de plataforma para banco de dados"""
    __tablename__ = "platforms"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True)  # youtube, instagram, tiktok, facebook, kwai
    credentials = Column(Text, nullable=True)  # JSON com credenciais
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PlatformDB(id={self.id}, name={self.name}, enabled={self.enabled})>"