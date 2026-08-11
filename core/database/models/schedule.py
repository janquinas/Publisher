"""
Modelo de Agendamento do Banco de Dados
"""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from core.database.config import Base


class ScheduleDB(Base):
    """Modelo de agendamento para banco de dados"""
    __tablename__ = "schedules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    publication_id = Column(String(36), ForeignKey("publications.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, completed, failed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    
    # Relacionamentos
    publication = relationship("PublicationDB", back_populates="schedules")
    
    def __repr__(self):
        return f"<ScheduleDB(id={self.id}, scheduled_at={self.scheduled_at}, status={self.status})>"