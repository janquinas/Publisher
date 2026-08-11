"""
Modelo de Plataforma
"""
from pydantic import BaseModel, Field
from typing import Dict


class Platform(BaseModel):
    """Representa uma plataforma de publicação"""
    name: str = Field(..., description="Nome da plataforma: youtube, instagram, tiktok, facebook, kwai")
    credentials: Dict[str, str] = Field(default_factory=dict, description="Credenciais de autenticação")
    enabled: bool = Field(default=True, description="Se a plataforma está habilitada para publicação")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "youtube",
                "credentials": {
                    "api_key": "chave_api_youtube",
                    "access_token": "token_acesso"
                },
                "enabled": True
            }
        }
