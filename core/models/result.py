"""
Modelo de Resultado
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Result(BaseModel):
    """Representa o resultado de uma publicação"""
    id: Optional[str] = None
    platform_name: str = Field(..., description="Nome da plataforma")
    success: bool = Field(..., description="Se a publicação foi bem-sucedida")
    message: str = Field(..., description="Mensagem de resultado ou erro")
    post_url: Optional[str] = Field(None, description="URL da publicação (se bem-sucedida)")
    error_code: Optional[str] = Field(None, description="Código do erro (se houver)")
    published_at: Optional[datetime] = Field(None, description="Data e hora da publicação")
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "platform_name": "youtube",
                "success": True,
                "message": "Vídeo publicado com sucesso",
                "post_url": "https://youtube.com/watch?v=abc123",
                "published_at": "2024-12-25T10:05:00"
            }
        }