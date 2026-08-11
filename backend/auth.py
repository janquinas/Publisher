"""
Dependency de autenticacao — verifica token em endpoints protegidos.

As sessões são persistidas no banco de dados (tabela sessions).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict

from core.database.config import SessionLocal
from core.database.repositories.session_repository import SessionRepository

_bearer = HTTPBearer(auto_error=False)


def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Dict:
    """
    Dependency que valida o Bearer token consultando o banco de dados
    e retorna os dados da sessão.

    Uso nos endpoints:
        async def meu_endpoint(session=Depends(get_current_session)):
            user_id = session["user_id"]

    Raises:
        HTTPException 401: se o token estiver ausente, inválido ou expirado.
    """
    token = credentials.credentials if credentials else None
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao autenticado. Faca login e envie o token no header Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db = SessionLocal()
    try:
        repo = SessionRepository(db)
        sess = repo.get_by_token(token)
    finally:
        db.close()

    if not sess:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessao invalida ou expirada. Faca login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id":       sess.user_id,
        "name":          sess.user_name,
        "email":         sess.user_email,
        "profile_photo": sess.user_photo,
    }
