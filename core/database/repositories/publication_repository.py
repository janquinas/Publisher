"""
Repository de Publicações
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from core.database.models.publication import PublicationDB
from core.database.models.schedule import ScheduleDB
from core.database.models.result import ResultDB


class PublicationRepository:
    """Repositório para operações com publicações"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        title: str,
        description: str,
        media_path: str,
        media_size_mb: str,
        media_format: str,
        duration_seconds: Optional[str] = None,
        thumbnail_path: Optional[str] = None,
        platforms: Optional[str] = None,
        is_media_only: bool = False,
    ) -> PublicationDB:
        """
        Cria uma nova publicação ou entrada de biblioteca de mídia.

        Args:
            title: Título
            description: Descrição
            media_path: Nome do arquivo salvo no disco
            media_size_mb: Tamanho em MB (string)
            media_format: Extensão do arquivo (mp4, etc.)
            duration_seconds: Duração em segundos (opcional)
            thumbnail_path: Caminho da thumbnail (opcional)
            platforms: JSON string com lista de plataformas (opcional)
            is_media_only: True = upload de biblioteca; False = publicação agendada

        Returns:
            PublicationDB criada
        """
        import json as _json
        publication = PublicationDB(
            title=title,
            description=description,
            media_path=media_path,
            media_size_mb=media_size_mb,
            media_format=media_format,
            duration_seconds=duration_seconds,
            thumbnail_path=thumbnail_path,
            platforms=platforms if platforms is not None else _json.dumps([]),
            is_media_only=is_media_only,
        )
        self.db.add(publication)
        self.db.commit()
        self.db.refresh(publication)
        return publication

    def get_by_id(self, publication_id: str) -> Optional[PublicationDB]:
        """Busca publicação por ID (qualquer tipo)."""
        return self.db.query(PublicationDB).filter(
            PublicationDB.id == publication_id
        ).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[PublicationDB]:
        """Lista publicações agendadas (is_media_only=False)."""
        return (
            self.db.query(PublicationDB)
            .filter(PublicationDB.is_media_only == False)  # noqa: E712
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_media(self, skip: int = 0, limit: int = 100) -> List[PublicationDB]:
        """Lista entradas da biblioteca de mídia (is_media_only=True)."""
        return (
            self.db.query(PublicationDB)
            .filter(PublicationDB.is_media_only == True)  # noqa: E712
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, publication_id: str, **kwargs) -> Optional[PublicationDB]:
        """Atualiza campos de uma publicação."""
        publication = self.get_by_id(publication_id)
        if not publication:
            return None
        for key, value in kwargs.items():
            if hasattr(publication, key):
                setattr(publication, key, value)
        publication.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(publication)
        return publication

    def delete(self, publication_id: str) -> bool:
        """Remove uma publicação. Retorna True se removida."""
        publication = self.get_by_id(publication_id)
        if not publication:
            return False
        self.db.delete(publication)
        self.db.commit()
        return True

    def add_schedule(
        self,
        publication_id: str,
        scheduled_at: datetime,
        status: str = "pending",
    ) -> Optional[ScheduleDB]:
        """Adiciona um agendamento a uma publicação."""
        publication = self.get_by_id(publication_id)
        if not publication:
            return None
        schedule = ScheduleDB(
            publication_id=publication_id,
            scheduled_at=scheduled_at,
            status=status,
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def add_result(
        self,
        publication_id: str,
        platform_name: str,
        success: bool,
        message: str,
        post_url: Optional[str] = None,
        error_code: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ) -> Optional[ResultDB]:
        """Adiciona um resultado a uma publicação."""
        publication = self.get_by_id(publication_id)
        if not publication:
            return None
        result = ResultDB(
            publication_id=publication_id,
            platform_name=platform_name,
            success=success,
            message=message,
            post_url=post_url,
            error_code=error_code,
            published_at=published_at,
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result
