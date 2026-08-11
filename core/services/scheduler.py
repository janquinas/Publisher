"""
Scheduler - Gerenciamento de agendamento de publicações
"""
from typing import Dict, List, Optional, Callable
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from ..models.schedule import Schedule
from .log_manager import get_log_manager


class Scheduler:
    """Gerenciador de agendamento de publicações"""
    
    def __init__(self):
        self.logger = get_log_manager("core.scheduler")
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.scheduled_jobs: Dict[str, str] = {}  # publication_id -> job_id
        self.logger.info("Scheduler inicializado")
    
    def schedule_publication(self, publication_id: str, scheduled_at: datetime, 
                           callback: Callable) -> bool:
        """
        Agenda uma publicação para execução
        
        Args:
            publication_id: ID da publicação
            scheduled_at: Data e hora da publicação
            callback: Função a ser chamada no horário agendado
            
        Returns:
            bool: True se agendado com sucesso
        """
        try:
            self.logger.info(
                "Agendando publicação",
                publication_id=publication_id,
                scheduled_at=scheduled_at.isoformat()
            )
            
            # Criar trigger para a data/hora específica
            trigger = DateTrigger(run_date=scheduled_at)
            
            # Adicionar job ao scheduler
            job = self.scheduler.add_job(
                callback,
                trigger=trigger,
                id=publication_id,
                replace_existing=True
            )
            
            # Registrar job
            self.scheduled_jobs[publication_id] = job.id
            
            self.logger.info(
                "Publicação agendada com sucesso",
                publication_id=publication_id,
                job_id=job.id,
                scheduled_at=scheduled_at.isoformat()
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Erro ao agendar publicação",
                publication_id=publication_id,
                error=str(e)
            )
            return False
    
    def cancel_publication(self, publication_id: str) -> bool:
        """
        Cancela uma publicação agendada
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            bool: True se cancelado com sucesso
        """
        try:
            if publication_id in self.scheduled_jobs:
                job_id = self.scheduled_jobs[publication_id]
                self.scheduler.remove_job(job_id)
                del self.scheduled_jobs[publication_id]
                
                self.logger.info(
                    "Publicação cancelada",
                    publication_id=publication_id,
                    job_id=job_id
                )
                return True
            
            self.logger.warning(
                "Publicação não encontrada para cancelamento",
                publication_id=publication_id
            )
            return False
            
        except Exception as e:
            self.logger.error(
                "Erro ao cancelar publicação",
                publication_id=publication_id,
                error=str(e)
            )
            return False
    
    def get_scheduled_publications(self) -> List[Dict]:
        """
        Obtém lista de publicações agendadas
        
        Returns:
            Lista de publicações agendadas
        """
        scheduled = []
        
        for publication_id, job_id in self.scheduled_jobs.items():
            try:
                job = self.scheduler.get_job(job_id)
                if job:
                    scheduled.append({
                        "publication_id": publication_id,
                        "job_id": job_id,
                        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
                    })
            except Exception as e:
                self.logger.error(
                    "Erro ao obter informações do job",
                    publication_id=publication_id,
                    error=str(e)
                )
        
        return scheduled
    
    def is_scheduled(self, publication_id: str) -> bool:
        """
        Verifica se uma publicação está agendada
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            bool: True se está agendada
        """
        return publication_id in self.scheduled_jobs
    
    def get_next_run_time(self, publication_id: str) -> Optional[datetime]:
        """
        Obtém o próximo horário de execução de uma publicação
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            datetime ou None se não encontrado
        """
        try:
            if publication_id in self.scheduled_jobs:
                job_id = self.scheduled_jobs[publication_id]
                job = self.scheduler.get_job(job_id)
                if job and job.next_run_time:
                    return job.next_run_time
            return None
        except Exception as e:
            self.logger.error(
                "Erro ao obter próximo horário",
                publication_id=publication_id,
                error=str(e)
            )
            return None
    
    def shutdown(self):
        """Para o scheduler"""
        try:
            self.scheduler.shutdown()
            self.logger.info("Scheduler parado")
        except Exception as e:
            self.logger.error("Erro ao parar scheduler", error=str(e))