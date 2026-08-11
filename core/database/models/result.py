"""
Modelo de Resultado do Banco de Dados
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from core.database.config import Base


class ResultDB(Base):
    """Modelo de resultado para banco de dados"""
    __tablename__ = "results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    publication_id = Column(String(36), ForeignKey("publications.id"), nullable=False)
    platform_name = Column(String(50), nullable=False)
    success = Column(Boolean, nullable=False)
    message = Column(Text, nullable=False)
    post_url = Column(String(500), nullable=True)
    error_code = Column(String(50), nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    publication = relationship("PublicationDB", back_populates="results")
    
    def __repr__(self):
        return f"<ResultDB(id={self.id}, platform={self.platform_name}, success={self.success})>"