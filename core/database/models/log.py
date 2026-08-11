"""
Modelo de Log do Banco de Dados
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from core.database.config import Base


class LogDB(Base):
    """Modelo de log para banco de dados"""
    __tablename__ = "logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    publication_id = Column(String(36), ForeignKey("publications.id"), nullable=True)
    level = Column(String(20), nullable=False)  # INFO, ERROR, WARNING, DEBUG
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(Text, nullable=True)  # JSON com dados adicionais
    
    # Relacionamentos
    publication = relationship("PublicationDB", back_populates="logs")
    
    def __repr__(self):
        return f"<LogDB(id={self.id}, level={self.level}, module={self.module})>"