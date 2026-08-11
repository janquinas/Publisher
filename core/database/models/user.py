"""
Modelo de Usuário do Banco de Dados
"""
from sqlalchemy import Column, String, Text, DateTime
import uuid
from datetime import datetime
from core.database.config import Base


class UserDB(Base):
    """Modelo de usuário para banco de dados"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    password_hash = Column(String(200), nullable=False)
    profile_photo = Column(Text, nullable=True)
    reset_token = Column(String(128), nullable=True, unique=True)
    reset_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserDB(id={self.id}, name={self.name}, email={self.email})>"
