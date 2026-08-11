"""
Publication Orchestrator - Coordenador da execução das publicações
"""
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..models.publication import Publication
from ..models.platform import Platform
from ..models.result import Result
from ..adapters.base_adapter import BasePlatformAdapter
from .result_manager import ResultManager
from .log_manager import get_log_manager


class PublicationOrchestrator:
    """Coordenador da execução das publicações"""
    
    def __init__(self, result_manager: ResultManager):
        self.logger = get_log_manager("core.orchestrator")
        self.result_manager = result_manager
        self.result_manager.set_logger(self.logger)
        self.adapters: Dict[str, BasePlatformAdapter] = {}
    
    def register_adapter(self, platform_name: str, adapter: BasePlatformAdapter):
        """
        Registra um adaptador de plataforma
        
        Args:
            platform_name: Nome da plataforma
            adapter: Instância do adaptador
        """
        self.adapters[platform_name] = adapter
        self.logger.info("Adaptador registrado", platform=platform_name)
    
    def execute_publication(self, publication: Publication) -> Dict[str, Result]:
        """
        Executa a publicação em todas as plataformas selecionadas
        
        Args:
            publication: Objeto Publication com dados da publicação
            
        Returns:
            Dict com resultados por plataforma
        """
        publication_id = publication.id or "unknown"
        
        self.logger.log_publication_start(
            publication_id=publication_id,
            platforms=[p.name for p in publication.platforms]
        )
        
        results = {}
        
        # Filtrar apenas plataformas habilitadas
        enabled_platforms = [p for p in publication.platforms if p.enabled]
        
        if not enabled_platforms:
            self.logger.warning(
                "Nenhuma plataforma habilitada para publicação",
                publication_id=publication_id
            )
            return results
        
        # Executar publicações em paralelo
        with ThreadPoolExecutor(max_workers=len(enabled_platforms)) as executor:
            # Submeter tarefas
            future_to_platform = {}
            for platform in enabled_platforms:
                future = executor.submit(
                    self._publish_to_platform,
                    publication,
                    platform
                )
                future_to_platform[future] = platform.name
            
            # Coletar resultados
            for future in as_completed(future_to_platform):
                platform_name = future_to_platform[future]
                try:
                    result = future.result()
                    results[platform_name] = result
                    
                    # Adicionar ao ResultManager
                    self.result_manager.add_result(publication_id, result)
                    
                    # Log do resultado
                    self.logger.log_platform_result(
                        publication_id=publication_id,
                        platform=platform_name,
                        success=result.success,
                        message=result.message
                    )
                    
                except Exception as e:
                    self.logger.error(
                        "Erro ao executar publicação em plataforma",
                        publication_id=publication_id,
                        platform=platform_name,
                        error=str(e)
                    )
                    
                    # Criar resultado de erro
                    error_result = Result(
                        platform_name=platform_name,
                        success=False,
                        message=f"Erro inesperado: {str(e)}",
                        error_code="UNEXPECTED_ERROR"
                    )
                    results[platform_name] = error_result
                    self.result_manager.add_result(publication_id, error_result)
        
        # Log de conclusão
        summary = self.result_manager.get_summary(publication_id)
        self.logger.log_publication_end(
            publication_id=publication_id,
            success=summary['all_success'],
            results=summary
        )
        
        return results
    
    def _publish_to_platform(self, publication: Publication, platform: Platform) -> Result:
        """
        Publica em uma plataforma específica.
        Carrega as credenciais reais do banco antes de chamar o adapter.
        """
        adapter = self.adapters.get(platform.name)

        if not adapter:
            return Result(
                platform_name=platform.name,
                success=False,
                message=f"Adaptador não encontrado para plataforma: {platform.name}",
                error_code="ADAPTER_NOT_FOUND",
            )

        # Carregar credenciais reais do banco (substituem as {} do objeto Publication)
        credentials = self._load_platform_credentials(platform.name) or platform.credentials or {}

        if not credentials:
            return Result(
                platform_name=platform.name,
                success=False,
                message=f"Plataforma '{platform.name}' não está conectada. "
                        f"Vá em Conexões e autorize o acesso.",
                error_code="NOT_CONNECTED",
            )

        # Injetar logger no adapter
        adapter.set_logger(self.logger.logger)

        return adapter.publish(
            media=publication.media,
            title=publication.title,
            description=publication.description,
            credentials=credentials,
        )

    def _load_platform_credentials(self, platform_name: str) -> Optional[dict]:
        """
        Carrega credenciais da plataforma diretamente do banco.
        Retorna None se a plataforma não estiver conectada.
        """
        try:
            if not hasattr(self, "db_integration") or self.db_integration is None:
                return None
            platform_db = self.db_integration.platform_repo.get_by_name(platform_name)
            if not platform_db or not platform_db.credentials:
                return None
            import json
            creds = platform_db.credentials
            if isinstance(creds, str):
                creds = json.loads(creds)
            return creds if creds else None
        except Exception as e:
            self.logger.error(
                f"Erro ao carregar credenciais de {platform_name}: {e}"
            )
            return None
    
    def get_publication_status(self, publication_id: str) -> Dict:
        """
        Obtém status de uma publicação
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            Dict com status da publicação
        """
        results = self.result_manager.get_results(publication_id)
        
        if not results:
            return {
                "publication_id": publication_id,
                "status": "not_found",
                "message": "Publicação não encontrada"
            }
        
        summary = self.result_manager.get_summary(publication_id)
        
        return {
            "publication_id": publication_id,
            "status": "completed",
            "summary": summary,
            "results": [
                {
                    "platform": r.platform_name,
                    "success": r.success,
                    "message": r.message,
                    "post_url": r.post_url
                }
                for r in results
            ]
        }
    
    def retry_failed_publications(self, publication_id: str, publication: Publication) -> Dict[str, Result]:
        """
        Retenta publicações que falharam
        
        Args:
            publication_id: ID da publicação
            publication: Dados da publicação
            
        Returns:
            Dict com resultados das retentativas
        """
        self.logger.info(
            "Iniciando retentativa de publicações falhas",
            publication_id=publication_id
        )
        
        # Obter apenas resultados de falha
        failed_results = self.result_manager.get_failed_results(publication_id)
        failed_platforms = [r.platform_name for r in failed_results]
        
        # Filtrar plataformas que falharam
        platforms_to_retry = [
            p for p in publication.platforms 
            if p.name in failed_platforms and p.enabled
        ]
        
        if not platforms_to_retry:
            self.logger.info(
                "Nenhuma plataforma para retentar",
                publication_id=publication_id
            )
            return {}
        
        # Executar retentativas
        retry_results = {}
        for platform in platforms_to_retry:
            self.logger.info(
                "Retentando publicação",
                publication_id=publication_id,
                platform=platform.name
            )
            
            result = self._publish_to_platform(publication, platform)
            retry_results[platform.name] = result
            
            # Atualizar resultado no ResultManager
            self.result_manager.add_result(publication_id, result)
        
        return retry_results