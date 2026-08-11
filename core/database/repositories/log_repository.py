"""
Repository de Logs
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from core.database.models.log import LogDB


class LogRepository:
    """Repositório para operações com logs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, level: str, message: str, module: str,
               publication_id: Optional[str] = None,
               extra_data: Optional[str] = None) -> LogDB:
        """
        Cria um novo log
        
        Args:
            level: Nível do log (INFO, ERROR, WARNING, DEBUG)
            message: Mensagem do log
            module: Módulo que gerou o log
            publication_id: ID da publicação (opcional)
            extra_data: Dados adicionais em JSON (opcional)
            
        Returns:
            LogDB: Log criado
        """
        log = LogDB(
            level=level,
            message=message,
            module=module,
            publication_id=publication_id,
            extra_data=extra_data
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        return log
    
    def get_by_id(self, log_id: str) -> Optional[LogDB]:
        """
        Busca log por ID
        
        Args:
            log_id: ID do log
            
        Returns:
            LogDB ou None
        """
        return self.db.query(LogDB).filter(
            LogDB.id == log_id
        ).first()
    
    def get_by_publication_id(self, publication_id: str) -> List[LogDB]:
        """
        Busca logs por ID da publicação
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            Lista de logs
        """
        return self.db.query(LogDB).filter(
            LogDB.publication_id == publication_id
        ).order_by(LogDB.timestamp.desc()).all()
    
    def get_by_level(self, level: str, limit: int = 100) -> List[LogDB]:
        """
        Busca logs por nível
        
        Args:
            level: Nível do log
            limit: Limite de registros
            
        Returns:
            Lista de logs
        """
        return self.db.query(LogDB).filter(
            LogDB.level == level
        ).order_by(LogDB.timestamp.desc()).limit(limit).all()
    
    def get_by_module(self, module: str, limit: int = 100) -> List[LogDB]:
        """
        Busca logs por módulo
        
        Args:
            module: Nome do módulo
            limit: Limite de registros
            
        Returns:
            Lista de logs
        """
        return self.db.query(LogDB).filter(
            LogDB.module == module
        ).order_by(LogDB.timestamp.desc()).limit(limit).all()
    
    def get_recent_logs(self, limit: int = 100) -> List[LogDB]:
        """
        Busca logs mais recentes
        
        Args:
            limit: Limite de registros
            
        Returns:
            Lista de logs
        """
        return self.db.query(LogDB).order_by(
            LogDB.timestamp.desc()
        ).limit(limit).all()
    
    def delete_old_logs(self, days: int = 30) -> int:
        """
        Remove logs antigos
        
        Args:
            days: Número de dias para manter
            
        Returns:
            Número de logs removidos
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted = self.db.query(LogDB).filter(
            LogDB.timestamp < cutoff_date
        ).delete()
        
        self.db.commit()
        
        return deleted