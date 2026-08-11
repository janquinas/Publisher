"""
Repository de Agendamentos
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from core.database.models.schedule import ScheduleDB


class ScheduleRepository:
    """Repositório para operações com agendamentos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, publication_id: str, scheduled_at: datetime, 
               status: str = "pending") -> ScheduleDB:
        """
        Cria um novo agendamento
        
        Args:
            publication_id: ID da publicação
            scheduled_at: Data/hora agendada
            status: Status do agendamento
            
        Returns:
            ScheduleDB: Agendamento criado
        """
        schedule = ScheduleDB(
            publication_id=publication_id,
            scheduled_at=scheduled_at,
            status=status
        )
        
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        
        return schedule
    
    def get_by_id(self, schedule_id: str) -> Optional[ScheduleDB]:
        """
        Busca agendamento por ID
        
        Args:
            schedule_id: ID do agendamento
            
        Returns:
            ScheduleDB ou None
        """
        return self.db.query(ScheduleDB).filter(
            ScheduleDB.id == schedule_id
        ).first()
    
    def get_by_publication_id(self, publication_id: str) -> List[ScheduleDB]:
        """
        Busca agendamentos por ID da publicação
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            Lista de agendamentos
        """
        return self.db.query(ScheduleDB).filter(
            ScheduleDB.publication_id == publication_id
        ).all()
    
    def get_pending_schedules(self) -> List[ScheduleDB]:
        """
        Busca todos os agendamentos pendentes
        
        Returns:
            Lista de agendamentos pendentes
        """
        return self.db.query(ScheduleDB).filter(
            ScheduleDB.status == "pending"
        ).all()
    
    def update_status(self, schedule_id: str, status: str, 
                      executed_at: Optional[datetime] = None) -> Optional[ScheduleDB]:
        """
        Atualiza status de um agendamento
        
        Args:
            schedule_id: ID do agendamento
            status: Novo status
            executed_at: Data/hora de execução (opcional)
            
        Returns:
            ScheduleDB atualizado ou None
        """
        schedule = self.get_by_id(schedule_id)
        if not schedule:
            return None
        
        schedule.status = status
        if executed_at:
            schedule.executed_at = executed_at
        
        self.db.commit()
        self.db.refresh(schedule)
        
        return schedule
    
    def delete(self, schedule_id: str) -> bool:
        """
        Remove um agendamento
        
        Args:
            schedule_id: ID do agendamento
            
        Returns:
            True se removido, False se não encontrado
        """
        schedule = self.get_by_id(schedule_id)
        if not schedule:
            return False
        
        self.db.delete(schedule)
        self.db.commit()
        
        return True