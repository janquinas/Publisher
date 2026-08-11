"""
Custom Exceptions - Exceções customizadas da aplicação
"""
from typing import Optional, Dict, Any


class BaseAPIException(Exception):
    """Exceção base da API"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """Erro de validação"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            details=details
        )


class NotFoundError(BaseAPIException):
    """Recurso não encontrado"""
    
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} não encontrado",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id}
        )


class UnauthorizedError(BaseAPIException):
    """Não autorizado"""
    
    def __init__(self, message: str = "Não autorizado"):
        super().__init__(
            message=message,
            status_code=401
        )


class ForbiddenError(BaseAPIException):
    """Acesso negado"""
    
    def __init__(self, message: str = "Acesso negado"):
        super().__init__(
            message=message,
            status_code=403
        )


class InternalServerError(BaseAPIException):
    """Erro interno do servidor"""
    
    def __init__(self, message: str = "Erro interno do servidor"):
        super().__init__(
            message=message,
            status_code=500
        )


class FileUploadError(BaseAPIException):
    """Erro no upload de arquivo"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            details=details
        )


class PlatformError(BaseAPIException):
    """Erro relacionado a plataforma"""
    
    def __init__(self, platform: str, message: str):
        super().__init__(
            message=f"Erro na plataforma {platform}: {message}",
            status_code=400,
            details={"platform": platform}
        )


class PublicationError(BaseAPIException):
    """Erro relacionado a publicação"""
    
    def __init__(self, message: str, publication_id: Optional[str] = None):
        details = {}
        if publication_id:
            details["publication_id"] = publication_id
        
        super().__init__(
            message=message,
            status_code=400,
            details=details
        )