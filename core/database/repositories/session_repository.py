"""
Repository de Sessões

Gerencia sessões autenticadas persistidas no banco de dados.
Substitui o dicionário _sessions em memória do auth_controller.
"""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session as DBSession

from core.database.models.session import SessionDB


class SessionRepository:
    """Repositório para operações com sessões de usuário."""

    def __init__(self, db: DBSession):
        self.db = db

    def create(
        self,
        token: str,
        user_id: str,
        user_name: str,
        user_email: str,
        user_photo: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> SessionDB:
        """Cria uma nova sessão."""
        session = SessionDB(
            token=token,
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            user_photo=user_photo,
            expires_at=expires_at,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_token(self, token: str) -> Optional[SessionDB]:
        """Busca sessão pelo token. Retorna None se não encontrada ou expirada."""
        session = (
            self.db.query(SessionDB)
            .filter(SessionDB.token == token)
            .first()
        )
        if session is None:
            return None
        # Verificar expiração
        if session.expires_at and session.expires_at < datetime.utcnow():
            self.delete_by_token(token)
            return None
        return session

    def delete_by_token(self, token: str) -> bool:
        """Remove sessão pelo token. Retorna True se removida."""
        deleted = (
            self.db.query(SessionDB)
            .filter(SessionDB.token == token)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted > 0

    def delete_by_user_id(self, user_id: str) -> int:
        """Remove todas as sessões de um usuário. Retorna quantidade removida."""
        deleted = (
            self.db.query(SessionDB)
            .filter(SessionDB.user_id == user_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted

    def update_user_photo(self, user_id: str, photo: str) -> int:
        """Atualiza a foto em todas as sessões ativas de um usuário."""
        updated = (
            self.db.query(SessionDB)
            .filter(SessionDB.user_id == user_id)
            .update({"user_photo": photo}, synchronize_session=False)
        )
        self.db.commit()
        return updated
