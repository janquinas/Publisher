"""
Integração do Backend com o Núcleo do Sistema
"""
from typing import Optional
from sqlalchemy.orm import Session

from core.services.publication_service import PublicationService
from core.services.scheduler import Scheduler
from core.services.orchestrator import PublicationOrchestrator
from core.services.result_manager import ResultManager
from core.services.media_manager import MediaManager
from core.database.integration import DatabaseIntegration
from core.services.log_manager import get_log_manager


class CoreIntegration:
    """
    Classe responsável por integrar o backend com o núcleo do sistema.
    Instanciada por request para garantir que a sessão de banco seja válida.
    """

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_log_manager("backend.core_integration")

        # Integração com banco de dados (por request)
        self.db_integration = DatabaseIntegration(db)

        # Serviços do núcleo (ordem: result_manager → orchestrator → publication_service)
        self.result_manager = ResultManager()
        self.media_manager = MediaManager()
        self.scheduler_service = _get_scheduler()
        self.orchestrator = PublicationOrchestrator(self.result_manager)
        self.publication_service = PublicationService(
            media_manager=self.media_manager,
            scheduler=self.scheduler_service,
            orchestrator=self.orchestrator,
            result_manager=self.result_manager,
        )

        # Injetar db_integration nos serviços que precisam de acesso ao banco
        self.publication_service.db_integration = self.db_integration
        self.orchestrator.db_integration = self.db_integration

        # Registrar adapters de plataforma no orchestrator
        self._register_adapters()

        self.logger.info("CoreIntegration inicializada para esta request")

    def get_publication_service(self) -> PublicationService:
        return self.publication_service

    def get_scheduler_service(self) -> Scheduler:
        return self.scheduler_service

    def get_orchestrator(self) -> PublicationOrchestrator:
        return self.orchestrator

    def get_database_integration(self) -> DatabaseIntegration:
        return self.db_integration

    def _register_adapters(self):
        """
        Registra os adapters de plataforma no orchestrator.
        Cada plataforma tem seu adapter — atualmente o YouTube tem integração real,
        os demais são simulados e serão implementados futuramente.
        """
        from core.adapters.youtube_adapter import YouTubeAdapter
        from core.adapters.instagram_adapter import InstagramAdapter
        from core.adapters.tiktok_adapter import TikTokAdapter
        from core.adapters.facebook_adapter import FacebookAdapter
        from core.adapters.kwai_adapter import KwaiAdapter

        self.orchestrator.register_adapter("youtube",   YouTubeAdapter())
        self.orchestrator.register_adapter("instagram", InstagramAdapter())
        self.orchestrator.register_adapter("tiktok",    TikTokAdapter())
        self.orchestrator.register_adapter("facebook",  FacebookAdapter())
        self.orchestrator.register_adapter("kwai",      KwaiAdapter())

        self.logger.info("Adapters de plataforma registrados")

    def initialize(self):
        """Inicializa banco e dados padrão (chamado apenas no startup)."""
        try:
            self.logger.info("Inicializando serviços do núcleo...")
            self.db_integration.init_database()
            self.logger.info("Serviços do núcleo inicializados com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar núcleo: {str(e)}")
            raise

    def shutdown(self):
        """Finaliza serviços (chamado apenas no shutdown da aplicação)."""
        try:
            self.logger.info("Finalizando serviços do núcleo...")
            self.scheduler_service.shutdown()
            self.db.close()
            self.logger.info("Serviços do núcleo finalizados")
        except Exception as e:
            self.logger.error(f"Erro ao finalizar núcleo: {str(e)}")


# ---------------------------------------------------------------------------
# Scheduler é o único componente que deve ser singleton — ele mantém os jobs
# em memória e não depende de sessão de banco.
# ---------------------------------------------------------------------------
_scheduler_singleton: Optional[Scheduler] = None


def _get_scheduler() -> Scheduler:
    """Retorna o singleton do scheduler (cria na primeira chamada)."""
    global _scheduler_singleton
    if _scheduler_singleton is None:
        _scheduler_singleton = Scheduler()
    return _scheduler_singleton


def get_core_integration(db: Session) -> CoreIntegration:
    """
    Cria uma nova instância de CoreIntegration para a request atual.
    Cada request recebe sua própria sessão de banco, evitando sessões stale.
    O scheduler é compartilhado via singleton separado.

    Args:
        db: Sessão do banco de dados injetada pelo FastAPI (Depends(get_db))

    Returns:
        CoreIntegration: Instância nova para esta request
    """
    return CoreIntegration(db)