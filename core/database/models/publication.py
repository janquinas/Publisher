"""
Modelo de Publicação do Banco de Dados
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from core.database.config import Base


class PublicationDB(Base):
    """Modelo de publicação para banco de dados"""
    __tablename__ = "publications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    media_path = Column(String(500), nullable=False)
    media_size_mb = Column(String(50), nullable=False)
    media_format = Column(String(10), nullable=False)
    duration_seconds = Column(String(20), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    # Plataformas armazenadas como JSON, ex: '["instagram","tiktok"]'
    platforms = Column(Text, nullable=True, default="[]")
    # True = entrada da biblioteca de mídia (upload sem agendamento)
    # False (padrão) = publicação agendada criada pelo usuário
    is_media_only = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    schedules = relationship("ScheduleDB", back_populates="publication", cascade="all, delete-orphan")
    results = relationship("ResultDB", back_populates="publication", cascade="all, delete-orphan")
    logs = relationship("LogDB", back_populates="publication", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PublicationDB(id={self.id}, title={self.title})>"