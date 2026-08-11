"""
Dependency de autenticacao - verifica token em endpoints protegidos
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict

# Importar o dicionario de sessoes do auth_controller
# (sessoes ficam em memoria; em producao migrar para Redis ou JWT)
from backend.controllers.auth_controller import _sessions

_bearer = HTTPBearer(auto_error=False)


def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Dict:
    """
    Dependency que valida o Bearer token e retorna os dados da sessao.

    Uso nos endpoints:
        async def meu_endpoint(session=Depends(get_current_session)):
            user_id = session["user_id"]

    Raises:
        HTTPException 401: se o token estiver ausente ou invalido
    """
    token = credentials.credentials if credentials else None
    if not token or token not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao autenticado. Faca login e envie o token no header Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _sessions[token]
