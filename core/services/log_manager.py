"""
Log Manager - Sistema de logging do núcleo
"""
import logging
import sys
from datetime import datetime
from typing import Optional
from ..config import LOG_LEVEL, LOG_FORMAT


class LogManager:
    """Gerenciador de logs do núcleo do sistema"""
    
    def __init__(self, name: str = "core"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Evitar duplicação de handlers
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, LOG_LEVEL))
            
            # Formatter
            formatter = logging.Formatter(LOG_FORMAT)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        """Registra mensagem de informação"""
        if kwargs:
            self.logger.info(f"{message} | {kwargs}")
        else:
            self.logger.info(message)
    
    def error(self, message: str, **kwargs):
        """Registra mensagem de erro"""
        # Extrair erro se presente
        error_msg = kwargs.pop('error', None)
        
        if error_msg:
            message = f"{message} | Error: {error_msg}"
        
        if kwargs:
            message = f"{message} | {kwargs}"
        
        self.logger.error(message)
    
    def warning(self, message: str, **kwargs):
        """Registra mensagem de aviso"""
        if kwargs:
            self.logger.warning(f"{message} | {kwargs}")
        else:
            self.logger.warning(message)
    
    def debug(self, message: str, **kwargs):
        """Registra mensagem de debug"""
        if kwargs:
            self.logger.debug(f"{message} | {kwargs}")
        else:
            self.logger.debug(message)
    
    def log_publication_start(self, publication_id: str, platforms: list):
        """Registra início de publicação"""
        self.info(
            f"Iniciando publicação",
            publication_id=publication_id,
            platforms=platforms,
            timestamp=datetime.now().isoformat()
        )
    
    def log_publication_end(self, publication_id: str, success: bool, results: dict):
        """Registra término de publicação"""
        status = "sucesso" if success else "falha"
        self.info(
            f"Publicação concluída com {status}",
            publication_id=publication_id,
            success=success,
            results_summary=results,
            timestamp=datetime.now().isoformat()
        )
    
    def log_platform_result(self, publication_id: str, platform: str, success: bool, message: str):
        """Registra resultado de publicação em plataforma específica"""
        status = "sucesso" if success else "falha"
        self.info(
            f"Publicação em {platform}: {status} | {message}",
            publication_id=publication_id,
            platform=platform,
            success=success,
            timestamp=datetime.now().isoformat()
        )
    
    def log_error(self, publication_id: str, error: str, exception: Optional[Exception] = None):
        """Registra erro durante publicação"""
        self.error(
            f"Erro na publicação",
            publication_id=publication_id,
            error=error,
            exception=str(exception) if exception else None,
            timestamp=datetime.now().isoformat()
        )
    
    def log_scheduler_event(self, event: str, publication_id: str, scheduled_at: str):
        """Registra eventos do scheduler"""
        self.info(
            f"Evento do scheduler: {event}",
            publication_id=publication_id,
            scheduled_at=scheduled_at,
            timestamp=datetime.now().isoformat()
        )


# Instâncias por nome (cada módulo tem seu próprio logger)
_log_managers: dict = {}


def get_log_manager(name: str = "core") -> LogManager:
    """Retorna instância do LogManager para o nome especificado."""
    if name not in _log_managers:
        _log_managers[name] = LogManager(name)
    return _log_managers[name]
