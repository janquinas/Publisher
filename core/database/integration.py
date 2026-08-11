"""
Integração do banco de dados com o núcleo do sistema
"""
from typing import Optional
from sqlalchemy.orm import Session
from core.database.repositories import (
    PublicationRepository,
    ScheduleRepository,
    ResultRepository,
    LogRepository,
    PlatformRepository
)
from core.services.log_manager import get_log_manager


class DatabaseIntegration:
    """
    Classe responsável por integrar o banco de dados com os serviços do núcleo
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.publication_repo = PublicationRepository(db)
        self.schedule_repo = ScheduleRepository(db)
        self.result_repo = ResultRepository(db)
        self.log_repo = LogRepository(db)
        self.platform_repo = PlatformRepository(db)
        self.logger = get_log_manager("core.database")
    
    def init_database(self):
        """
        Inicializa o banco de dados criando tabelas e dados iniciais
        """
        try:
            self.logger.info("Inicializando banco de dados...")
            
            # Criar tabelas
            from core.database.config import init_db
            init_db()
            
            # Criar plataformas padrão se não existirem
            self._create_default_platforms()
            
            self.logger.info("Banco de dados inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
            raise
    
    def _create_default_platforms(self):
        """
        Cria plataformas padrão se não existirem
        """
        default_platforms = [
            ("youtube", None, True),
            ("instagram", None, True),
            ("tiktok", None, True),
            ("facebook", None, True),
            ("kwai", None, True)
        ]
        
        for name, credentials, enabled in default_platforms:
            existing = self.platform_repo.get_by_name(name)
            if not existing:
                self.platform_repo.create(name, credentials, enabled)
                self.logger.info(f"Plataforma '{name}' criada")
    
    def save_publication(self, publication_id: str, title: str, description: str,
                        media_path: str, media_size_mb: str, media_format: str,
                        duration_seconds: Optional[str] = None,
                        thumbnail_path: Optional[str] = None):
        """
        Salva uma publicação no banco de dados
        
        Args:
            publication_id: ID da publicação
            title: Título
            description: Descrição
            media_path: Caminho do arquivo
            media_size_mb: Tamanho do arquivo
            media_format: Formato do arquivo
            duration_seconds: Duração em segundos (opcional)
            thumbnail_path: Caminho da thumbnail (opcional)
        """
        try:
            publication = self.publication_repo.create(
                title=title,
                description=description,
                media_path=media_path,
                media_size_mb=media_size_mb,
                media_format=media_format,
                duration_seconds=duration_seconds,
                thumbnail_path=thumbnail_path
            )
            
            self.logger.info(
                "Publicação salva no banco de dados",
                publication_id=str(publication.id),
                title=title
            )
            
            return publication
            
        except Exception as e:
            self.logger.error(
                f"Erro ao salvar publicação: {str(e)}",
                publication_id=publication_id
            )
            raise
    
    def save_schedule(self, publication_id: str, scheduled_at, status: str = "pending"):
        """
        Salva um agendamento no banco de dados
        
        Args:
            publication_id: ID da publicação
            scheduled_at: Data/hora agendada
            status: Status do agendamento
        """
        try:
            schedule = self.schedule_repo.create(
                publication_id=publication_id,
                scheduled_at=scheduled_at,
                status=status
            )
            
            self.logger.info(
                "Agendamento salvo no banco de dados",
                schedule_id=str(schedule.id),
                publication_id=publication_id
            )
            
            return schedule
            
        except Exception as e:
            self.logger.error(
                f"Erro ao salvar agendamento: {str(e)}",
                publication_id=publication_id
            )
            raise
    
    def save_result(self, publication_id: str, platform_name: str, success: bool,
                    message: str, post_url: Optional[str] = None,
                    error_code: Optional[str] = None,
                    published_at=None):
        """
        Salva um resultado no banco de dados
        
        Args:
            publication_id: ID da publicação
            platform_name: Nome da plataforma
            success: Se foi bem-sucedido
            message: Mensagem de resultado
            post_url: URL da publicação (opcional)
            error_code: Código de erro (opcional)
            published_at: Data/hora da publicação (opcional)
        """
        try:
            result = self.result_repo.create(
                publication_id=publication_id,
                platform_name=platform_name,
                success=success,
                message=message,
                post_url=post_url,
                error_code=error_code,
                published_at=published_at
            )
            
            self.logger.info(
                "Resultado salvo no banco de dados",
                result_id=str(result.id),
                publication_id=publication_id,
                platform=platform_name,
                success=success
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Erro ao salvar resultado: {str(e)}",
                publication_id=publication_id,
                platform=platform_name
            )
            raise
    
    def save_log(self, level: str, message: str, module: str,
                 publication_id: Optional[str] = None,
                 extra_data: Optional[str] = None):
        """
        Salva um log no banco de dados
        
        Args:
            level: Nível do log
            message: Mensagem do log
            module: Módulo que gerou o log
            publication_id: ID da publicação (opcional)
            extra_data: Dados adicionais (opcional)
        """
        try:
            log = self.log_repo.create(
                level=level,
                message=message,
                module=module,
                publication_id=publication_id,
                extra_data=extra_data
            )
            
            return log
            
        except Exception as e:
            self.logger.error(
                f"Erro ao salvar log: {str(e)}",
                module=module
            )
            raise