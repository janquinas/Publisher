"""
Exception Handlers - Handlers customizados para exceções
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime

from backend.exceptions.custom_exceptions import BaseAPIException


def _now() -> str:
    return datetime.utcnow().isoformat()


async def api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """
    Handler para exceções customizadas da API.
    Retorna tanto 'detail' quanto 'message' para compatibilidade com o frontend.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error": True,
            "message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "timestamp": _now()
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler para HTTPException do FastAPI.
    Retorna tanto 'detail' (padrão FastAPI) quanto 'message' para compatibilidade
    com o frontend que lê result.detail || result.message.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": _now()
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler para exceções genéricas não tratadas.
    Retorna tanto 'detail' quanto 'message' por compatibilidade.
    """
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor",
            "error": True,
            "message": "Erro interno do servidor",
            "status_code": 500,
            "timestamp": _now()
        }
    )


def setup_exception_handlers(app):
    """Configura todos os exception handlers na aplicação."""
    from backend.exceptions.custom_exceptions import BaseAPIException

    app.add_exception_handler(BaseAPIException, api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
