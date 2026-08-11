"""
Modelo de Sessão do Banco de Dados

Substitui o dicionário _sessions em memória do auth_controller.
Garante que sessões sobrevivam a reinícios do servidor.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from core.database.config import Base


class SessionDB(Base):
    """Sessão autenticada de um usuário."""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # Snapshot dos dados do usuário no momento da criação (evita JOIN a cada check)
    user_name = Column(String(100), nullable=False, default="")
    user_email = Column(String(200), nullable=False, default="")
    user_photo = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # NULL = sem expiração definida; pode ser usado no futuro para TTL
    expires_at = Column(DateTime, nullable=True)

    user = relationship("UserDB", lazy="joined")

    def __repr__(self):
        return f"<SessionDB(token={self.token[:8]}..., user_id={self.user_id})>"
