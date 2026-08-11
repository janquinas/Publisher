"""
Repository de Resultados
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from core.database.models.result import ResultDB


class ResultRepository:
    """Repositório para operações com resultados"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, publication_id: str, platform_name: str, success: bool,
               message: str, post_url: Optional[str] = None,
               error_code: Optional[str] = None,
               published_at: Optional[datetime] = None) -> ResultDB:
        """
        Cria um novo resultado

        Args:
            publication_id: ID da publicação
            platform_name: Nome da plataforma
            success: Se foi bem-sucedido
            message: Mensagem de resultado
            post_url: URL da publicação (opcional)
            error_code: Código de erro (opcional)
            published_at: Data/hora da publicação (opcional)

        Returns:
            ResultDB: Resultado criado
        """
        result = ResultDB(
            publication_id=publication_id,
            platform_name=platform_name,
            success=success,
            message=message,
            post_url=post_url,
            error_code=error_code,
            published_at=published_at
        )

        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)

        return result

    def get_by_id(self, result_id: str) -> Optional[ResultDB]:
        """
        Busca resultado por ID

        Args:
            result_id: ID do resultado

        Returns:
            ResultDB ou None
        """
        return self.db.query(ResultDB).filter(
            ResultDB.id == result_id
        ).first()

    def get_by_publication_id(self, publication_id: str) -> List[ResultDB]:
        """
        Busca resultados por ID da publicação

        Args:
            publication_id: ID da publicação

        Returns:
            Lista de resultados
        """
        return self.db.query(ResultDB).filter(
            ResultDB.publication_id == publication_id
        ).all()

    def get_by_platform(self, publication_id: str, platform_name: str) -> List[ResultDB]:
        """
        Busca resultados por publicação e plataforma

        Args:
            publication_id: ID da publicação
            platform_name: Nome da plataforma

        Returns:
            Lista de resultados
        """
        return self.db.query(ResultDB).filter(
            ResultDB.publication_id == publication_id,
            ResultDB.platform_name == platform_name
        ).all()

    def get_successful_by_publication(self, publication_id: str) -> List[ResultDB]:
        """
        Busca resultados bem-sucedidos de uma publicação

        Args:
            publication_id: ID da publicação

        Returns:
            Lista de resultados bem-sucedidos
        """
        return self.db.query(ResultDB).filter(
            ResultDB.publication_id == publication_id,
            ResultDB.success == True
        ).all()

    def get_failed_by_publication(self, publication_id: str) -> List[ResultDB]:
        """
        Busca resultados de falha de uma publicação

        Args:
            publication_id: ID da publicação

        Returns:
            Lista de resultados de falha
        """
        return self.db.query(ResultDB).filter(
            ResultDB.publication_id == publication_id,
            ResultDB.success == False
        ).all()

    def get_all(self) -> List[ResultDB]:
        """
        Lista todos os resultados

        Returns:
            Lista de todos os resultados
        """
        return self.db.query(ResultDB).order_by(ResultDB.created_at.desc()).all()

    def get_recent(self, limit: int = 100) -> List[ResultDB]:
        """
        Busca resultados mais recentes

        Args:
            limit: Limite de registros

        Returns:
            Lista de resultados recentes
        """
        return self.db.query(ResultDB).order_by(
            ResultDB.created_at.desc()
        ).limit(limit).all()
