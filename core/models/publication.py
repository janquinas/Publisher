"""
Modelo de Publicação
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .platform import Platform
from .media import Media
from .schedule import Schedule


class Publication(BaseModel):
    """Representa uma publicação de vídeo"""
    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(..., max_length=5000)
    media: Media
    platforms: List[Platform]
    schedule: Optional[Schedule] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Meu Vídeo Incrível",
                "description": "Descrição do vídeo",
                "media": {
                    "file_path": "/videos/video.mp4",
                    "file_size_mb": 50.5,
                    "format": "mp4"
                },
                "platforms": [
                    {"name": "youtube", "credentials": {}},
                    {"name": "instagram", "credentials": {}}
                ]
            }
        }