"""
Publication Service - Porta de entrada do núcleo do sistema.

Toda operação de CRUD persiste no banco via DatabaseIntegration.
O dicionário self.publications serve apenas como cache em memória
para publicações criadas na sessão atual (necessário para o scheduler
e orchestrator que operam sobre objetos Publication em memória).
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..models.publication import Publication
from ..models.schedule import Schedule
from ..models.media import Media
from ..models.platform import Platform
from .media_manager import MediaManager
from .scheduler import Scheduler
from .orchestrator import PublicationOrchestrator
from .result_manager import ResultManager
from .log_manager import get_log_manager


class PublicationService:
    """Serviço de publicação - porta de entrada do núcleo"""

    def __init__(
        self,
        media_manager: MediaManager,
        scheduler: Scheduler,
        orchestrator: PublicationOrchestrator,
        result_manager: ResultManager,
    ):
        self.logger = get_log_manager("core.publication_service")
        self.media_manager = media_manager
        self.scheduler = scheduler
        self.orchestrator = orchestrator
        self.result_manager = result_manager

        # Cache em memória para a sessão atual (complementa o banco)
        self.publications: Dict[str, Publication] = {}

        # Injetado pelo CoreIntegration após construção
        self.db_integration = None

        # Factory de callbacks para jobs agendados — injetado pelo CoreIntegration.
        # Quando presente, cada job abre uma sessão de banco nova e independente,
        # evitando uso de sessões stale da request original.
        # Assinatura: scheduled_job_callback_factory(publication_id: str) -> Callable
        self.scheduled_job_callback_factory = None

        self.logger.info("Publication Service inicializado")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    # Diretório base dos uploads — espelha UPLOAD_DIR do media_controller
    _UPLOAD_DIR = os.path.join("backend", "static", "uploads")

    def _resolve_media_path(self, raw_path: str) -> str:
        """
        Garante que o caminho de mídia passado para os adapters seja completo.

        O banco armazena apenas o nome do arquivo (ex: 'abc_video.mp4').
        Os adapters precisam do caminho relativo completo para abrir o arquivo
        (ex: 'backend/static/uploads/abc_video.mp4').

        Se o valor já contiver um separador de diretório (caminho completo ou
        relativo com subpasta), é retornado sem modificação para manter
        retrocompatibilidade com registros antigos.
        """
        if not raw_path:
            return raw_path
        if os.sep in raw_path or "/" in raw_path:
            return raw_path
        return os.path.join(self._UPLOAD_DIR, raw_path)

    def _db_to_publication(self, pub_db) -> Publication:
        """Converte PublicationDB (SQLAlchemy) → Publication (Pydantic)."""
        # Pegar o primeiro agendamento, se houver
        schedule = None
        if pub_db.schedules:
            s = pub_db.schedules[0]
            schedule = Schedule(
                id=str(s.id),
                scheduled_at=s.scheduled_at,
                status=s.status,
                created_at=s.created_at,
                executed_at=s.executed_at,
            )

        media = Media(
            file_path=self._resolve_media_path(pub_db.media_path or ""),
            file_size_mb=float(pub_db.media_size_mb or 0),
            format=pub_db.media_format or "mp4",
            duration_seconds=int(pub_db.duration_seconds) if pub_db.duration_seconds else None,
            thumbnail_path=pub_db.thumbnail_path,
        )

        # Carrega plataformas persistidas na coluna platforms (JSON)
        import json as _json
        platforms_list = []
        raw_platforms = getattr(pub_db, "platforms", None)
        if raw_platforms:
            try:
                names = _json.loads(raw_platforms)
                platforms_list = [
                    Platform(name=n, credentials={}, enabled=True)
                    for n in names if n
                ]
            except Exception:
                pass

        return Publication(
            id=str(pub_db.id),
            title=pub_db.title,
            description=pub_db.description,
            media=media,
            platforms=platforms_list,
            schedule=schedule,
            created_at=pub_db.created_at,
            updated_at=pub_db.updated_at,
        )

    def _require_db(self):
        """Lança erro claro se db_integration não foi injetado."""
        if self.db_integration is None:
            raise RuntimeError(
                "PublicationService.db_integration não foi injetado. "
                "Certifique-se de que CoreIntegration.initialize() foi chamado."
            )

    # ------------------------------------------------------------------
    # Criar
    # ------------------------------------------------------------------

    def create_publication(
        self,
        title: str,
        description: str,
        platforms: list,
        media_path: Optional[str] = None,
        media_size_mb: float = 0.0,
        media_format: str = "mp4",
        scheduled_at: Optional[datetime] = None,
        duration_seconds: Optional[int] = None,
        thumbnail_path: Optional[str] = None,
    ) -> Publication:
        """
        Cria uma nova publicação e persiste no banco de dados.

        Args:
            title: Título da publicação
            description: Descrição
            platforms: Lista de nomes de plataformas (str)
            media_path: Caminho do arquivo de vídeo (opcional)
            media_size_mb: Tamanho em MB
            media_format: Formato do arquivo
            scheduled_at: Data/hora de agendamento (opcional)
            duration_seconds: Duração em segundos (opcional)
            thumbnail_path: Caminho da thumbnail (opcional)

        Returns:
            Publication: objeto criado

        Raises:
            ValueError: se dados inválidos
        """
        self._require_db()
        try:
            self.logger.info("Criando nova publicação", title=title, platforms=platforms)

            # 1. Persistir no banco
            import json as _json
            pub_db = self.db_integration.publication_repo.create(
                title=title,
                description=description,
                media_path=media_path or "",
                media_size_mb=str(media_size_mb),
                media_format=media_format,
                duration_seconds=str(duration_seconds) if duration_seconds else None,
                thumbnail_path=thumbnail_path,
                platforms=_json.dumps([p.lower() if isinstance(p, str) else p.name for p in platforms]),
                is_media_only=False,  # publicação criada pelo usuário, não upload de biblioteca
            )
            publication_id = str(pub_db.id)

            # 2. Persistir agendamento se fornecido
            sched_db = None
            if scheduled_at:
                sched_db = self.db_integration.schedule_repo.create(
                    publication_id=publication_id,
                    scheduled_at=scheduled_at,
                    status="pending",
                )

            # 3. Montar objeto Publication em memória para o scheduler/orchestrator
            media = Media(
                file_path=self._resolve_media_path(media_path or ""),
                file_size_mb=media_size_mb,
                format=media_format,
                duration_seconds=duration_seconds,
                thumbnail_path=thumbnail_path,
            )

            platform_objects = [
                Platform(name=p.lower() if isinstance(p, str) else p.name, credentials={}, enabled=True)
                for p in platforms
            ]

            schedule = None
            if scheduled_at and sched_db:
                schedule = Schedule(
                    id=str(sched_db.id),
                    scheduled_at=scheduled_at,
                    status="pending",
                    created_at=sched_db.created_at,
                )

            publication = Publication(
                id=publication_id,
                title=title,
                description=description,
                media=media,
                platforms=platform_objects,
                schedule=schedule,
                created_at=pub_db.created_at,
            )

            # 4. Guardar no cache em memória
            self.publications[publication_id] = publication

            # 5. Agendar ou executar imediatamente
            if schedule and scheduled_at:
                # Usar o factory de callbacks seguros quando disponível.
                # O factory cria um closure que abre sessão de banco nova a cada
                # execução, evitando sessões stale da request atual.
                if self.scheduled_job_callback_factory:
                    job_callback = self.scheduled_job_callback_factory(publication_id)
                else:
                    # Fallback: lambda direta (válida apenas para publish_now/testes)
                    job_callback = lambda: self._execute_scheduled_publication(publication_id)

                self.scheduler.schedule_publication(
                    publication_id=publication_id,
                    scheduled_at=scheduled_at,
                    callback=job_callback,
                )
                self.logger.info(
                    "Publicação agendada",
                    publication_id=publication_id,
                    scheduled_at=scheduled_at.isoformat(),
                )
            # Quando não há agendamento, não executa automaticamente —
            # o usuário dispara via POST /{id}/publish

            self.logger.info("Publicação criada com sucesso", publication_id=publication_id)
            return publication

        except Exception as e:
            self.logger.error("Erro ao criar publicação", error=str(e))
            raise ValueError(f"Erro ao criar publicação: {str(e)}")

    # ------------------------------------------------------------------
    # Ler
    # ------------------------------------------------------------------

    def get_publication(self, publication_id: str) -> Optional[Publication]:
        """Retorna publicação pelo ID; consulta o banco se não estiver em cache."""
        # 1. Tentar cache
        if publication_id in self.publications:
            return self.publications[publication_id]

        # 2. Consultar banco
        if self.db_integration:
            pub_db = self.db_integration.publication_repo.get_by_id(publication_id)
            if pub_db:
                pub = self._db_to_publication(pub_db)
                self.publications[publication_id] = pub
                return pub

        return None

    def list_publications(self) -> List[Publication]:
        """
        Lista todas as publicações vindas do banco de dados.
        Sincroniza o cache em memória com o resultado.
        """
        if self.db_integration:
            pubs_db = self.db_integration.publication_repo.get_all()
            result = []
            for pub_db in pubs_db:
                pub = self._db_to_publication(pub_db)
                self.publications[str(pub_db.id)] = pub
                result.append(pub)
            return result

        # Fallback para cache se db_integration não disponível
        return list(self.publications.values())

    # ------------------------------------------------------------------
    # Atualizar (tarefa 5)
    # ------------------------------------------------------------------

    def update_publication(
        self,
        publication_id: str,
        title: str,
        description: str,
        platforms: list,
        scheduled_at: Optional[datetime] = None,
    ) -> Optional[Publication]:
        """
        Atualiza título, descrição, plataformas e agendamento de uma publicação.

        Args:
            publication_id: ID da publicação
            title: Novo título
            description: Nova descrição
            platforms: Nova lista de plataformas
            scheduled_at: Nova data/hora de agendamento (None mantém existente)

        Returns:
            Publication atualizada ou None se não encontrada
        """
        self._require_db()
        try:
            # 1. Verificar existência no banco
            pub_db = self.db_integration.publication_repo.get_by_id(publication_id)
            if not pub_db:
                self.logger.warning("Publicação não encontrada para atualização", publication_id=publication_id)
                return None

            # 2. Atualizar campos no banco
            import json as _json
            self.db_integration.publication_repo.update(
                publication_id,
                title=title,
                description=description,
                platforms=_json.dumps([p.lower() if isinstance(p, str) else p.name for p in platforms]),
            )

            # 3. Atualizar agendamento se fornecido
            if scheduled_at:
                # Cancelar job anterior no scheduler, se houver
                if publication_id in self.publications and self.publications[publication_id].schedule:
                    self.scheduler.cancel_publication(publication_id)

                # Remover schedules antigos e criar novo
                existing_schedules = self.db_integration.schedule_repo.get_by_publication_id(publication_id)
                for s in existing_schedules:
                    self.db_integration.schedule_repo.delete(str(s.id))

                sched_db = self.db_integration.schedule_repo.create(
                    publication_id=publication_id,
                    scheduled_at=scheduled_at,
                    status="pending",
                )

                # Re-agendar no scheduler usando callback seguro quando disponível
                if self.scheduled_job_callback_factory:
                    update_job_callback = self.scheduled_job_callback_factory(publication_id)
                else:
                    update_job_callback = lambda: self._execute_scheduled_publication(publication_id)

                self.scheduler.schedule_publication(
                    publication_id=publication_id,
                    scheduled_at=scheduled_at,
                    callback=update_job_callback,
                )

            # 4. Reconstruir objeto Publication e atualizar cache
            pub_db_updated = self.db_integration.publication_repo.get_by_id(publication_id)
            pub = self._db_to_publication(pub_db_updated)

            # Manter plataformas passadas (não persistidas no banco por enquanto)
            platform_objects = [
                Platform(name=p.lower() if isinstance(p, str) else p.name, credentials={}, enabled=True)
                for p in platforms
            ]
            pub = pub.model_copy(update={"platforms": platform_objects})
            self.publications[publication_id] = pub

            self.logger.info("Publicação atualizada com sucesso", publication_id=publication_id)
            return pub

        except Exception as e:
            self.logger.error("Erro ao atualizar publicação", publication_id=publication_id, error=str(e))
            raise ValueError(f"Erro ao atualizar publicação: {str(e)}")

    # ------------------------------------------------------------------
    # Deletar (tarefa 5)
    # ------------------------------------------------------------------

    def delete_publication(self, publication_id: str) -> bool:
        """
        Remove uma publicação do banco e do cache.

        Args:
            publication_id: ID da publicação

        Returns:
            True se removida, False se não encontrada
        """
        self._require_db()
        try:
            # Cancelar agendamento ativo, se houver
            if publication_id in self.publications:
                self.scheduler.cancel_publication(publication_id)
                del self.publications[publication_id]

            deleted = self.db_integration.publication_repo.delete(publication_id)

            if deleted:
                self.logger.info("Publicação removida com sucesso", publication_id=publication_id)
            else:
                self.logger.warning("Publicação não encontrada para remoção", publication_id=publication_id)

            return deleted

        except Exception as e:
            self.logger.error("Erro ao remover publicação", publication_id=publication_id, error=str(e))
            raise ValueError(f"Erro ao remover publicação: {str(e)}")

    # ------------------------------------------------------------------
    # Publicar imediatamente (tarefa 5 — método estava ausente)
    # ------------------------------------------------------------------

    def publish_now(self, publication_id: str) -> Optional[Publication]:
        """
        Executa a publicação imediatamente (ignora agendamento).

        Args:
            publication_id: ID da publicação

        Returns:
            Publication com status atualizado ou None se não encontrada
        """
        publication = self.get_publication(publication_id)
        if not publication:
            return None

        self._execute_scheduled_publication(publication_id)
        return self.publications.get(publication_id)

    # ------------------------------------------------------------------
    # Cancelar
    # ------------------------------------------------------------------

    def cancel_publication(self, publication_id: str) -> bool:
        """
        Cancela uma publicação agendada.

        Args:
            publication_id: ID da publicação

        Returns:
            True se cancelada, False caso contrário
        """
        try:
            publication = self.get_publication(publication_id)
            if not publication:
                self.logger.warning("Publicação não encontrada para cancelamento", publication_id=publication_id)
                return False

            # Cancelar no scheduler (pode não estar agendado se já executou)
            self.scheduler.cancel_publication(publication_id)

            # Atualizar status no banco
            if self.db_integration:
                schedules = self.db_integration.schedule_repo.get_by_publication_id(publication_id)
                for s in schedules:
                    if s.status == "pending":
                        self.db_integration.schedule_repo.update_status(str(s.id), "cancelled")

            # Atualizar cache
            if publication.schedule:
                publication.schedule.status = "cancelled"

            self.logger.info("Publicação cancelada com sucesso", publication_id=publication_id)
            return True

        except Exception as e:
            self.logger.error("Erro ao cancelar publicação", publication_id=publication_id, error=str(e))
            return False

    # ------------------------------------------------------------------
    # Execução interna (agendada ou imediata)
    # ------------------------------------------------------------------

    def _execute_scheduled_publication(self, publication_id: str):
        """Executa a publicação via orchestrator e persiste o resultado."""
        try:
            self.logger.info("Executando publicação", publication_id=publication_id)

            publication = self.publications.get(publication_id)
            if not publication:
                # Tentar carregar do banco
                publication = self.get_publication(publication_id)
            if not publication:
                self.logger.error("Publicação não encontrada para execução", publication_id=publication_id)
                return

            # Executar via orchestrator
            results = self.orchestrator.execute_publication(publication)

            # Atualizar status do agendamento no banco
            if self.db_integration:
                schedules = self.db_integration.schedule_repo.get_by_publication_id(publication_id)
                for s in schedules:
                    if s.status == "pending":
                        self.db_integration.schedule_repo.update_status(
                            str(s.id), "completed", executed_at=datetime.utcnow()
                        )

            # Atualizar cache
            if publication.schedule:
                publication.schedule.status = "completed"
                publication.schedule.executed_at = datetime.utcnow()

            self.logger.info(
                "Publicação executada com sucesso",
                publication_id=publication_id,
                results_count=len(results),
            )

        except Exception as e:
            self.logger.error("Erro ao executar publicação", publication_id=publication_id, error=str(e))

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def get_publication_status(self, publication_id: str) -> Dict[str, Any]:
        """Retorna status resumido de uma publicação."""
        publication = self.get_publication(publication_id)
        if not publication:
            return {"publication_id": publication_id, "status": "not_found", "message": "Publicação não encontrada"}

        results_summary = self.result_manager.get_summary(publication_id)
        return {
            "publication_id": publication_id,
            "title": publication.title,
            "status": publication.schedule.status if publication.schedule else "pending",
            "scheduled_at": publication.schedule.scheduled_at.isoformat() if publication.schedule else None,
            "executed_at": (
                publication.schedule.executed_at.isoformat()
                if publication.schedule and publication.schedule.executed_at
                else None
            ),
            "platforms": [p.name for p in publication.platforms],
            "results": results_summary,
        }

    def retry_publication(self, publication_id: str) -> Dict[str, Any]:
        """Retenta publicações que falharam."""
        try:
            publication = self.get_publication(publication_id)
            if not publication:
                return {"success": False, "message": "Publicação não encontrada"}

            self.logger.info("Iniciando retentativa", publication_id=publication_id)
            retry_results = self.orchestrator.retry_failed_publications(
                publication_id=publication_id, publication=publication
            )
            return {"success": True, "publication_id": publication_id, "retry_results": retry_results}

        except Exception as e:
            self.logger.error("Erro ao retentar publicação", publication_id=publication_id, error=str(e))
            return {"success": False, "message": str(e)}

    def get_publication_report(self, publication_id: str) -> str:
        """Relatório detalhado de uma publicação."""
        return self.result_manager.get_detailed_report(publication_id)
