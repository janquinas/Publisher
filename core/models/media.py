"""
Modelo de Mídia
"""
from pydantic import BaseModel, Field
from typing import Optional


class Media(BaseModel):
    """Representa um arquivo de mídia (vídeo)"""
    file_path: str = Field(..., description="Caminho do arquivo de vídeo")
    file_size_mb: float = Field(..., ge=0, description="Tamanho do arquivo em MB")
    format: str = Field(..., description="Formato do arquivo: mp4, mov, avi, mkv")
    duration_seconds: Optional[int] = Field(None, description="Duração do vídeo em segundos")
    thumbnail_path: Optional[str] = Field(None, description="Caminho da thumbnail (se houver)")

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/videos/video.mp4",
                "file_size_mb": 50.5,
                "format": "mp4",
                "duration_seconds": 120,
                "thumbnail_path": "/videos/thumbnail.jpg"
            }
        }