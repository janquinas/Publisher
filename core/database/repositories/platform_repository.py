"""
Repository de Plataformas
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from core.database.models.platform import PlatformDB


class PlatformRepository:
    """Repositório para operações com plataformas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, name: str, credentials: Optional[str] = None, 
               enabled: bool = True) -> PlatformDB:
        """
        Cria uma nova plataforma
        
        Args:
            name: Nome da plataforma
            credentials: Credenciais em JSON (opcional)
            enabled: Se está habilitada
            
        Returns:
            PlatformDB: Plataforma criada
        """
        platform = PlatformDB(
            name=name,
            credentials=credentials,
            enabled=enabled
        )
        
        self.db.add(platform)
        self.db.commit()
        self.db.refresh(platform)
        
        return platform
    
    def get_by_id(self, platform_id: str) -> Optional[PlatformDB]:
        """
        Busca plataforma por ID
        
        Args:
            platform_id: ID da plataforma
            
        Returns:
            PlatformDB ou None
        """
        return self.db.query(PlatformDB).filter(
            PlatformDB.id == platform_id
        ).first()
    
    def get_by_name(self, name: str) -> Optional[PlatformDB]:
        """
        Busca plataforma por nome
        
        Args:
            name: Nome da plataforma
            
        Returns:
            PlatformDB ou None
        """
        return self.db.query(PlatformDB).filter(
            PlatformDB.name == name
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[PlatformDB]:
        """
        Lista todas as plataformas
        
        Args:
            skip: Número de registros para pular
            limit: Limite de registros
            
        Returns:
            Lista de plataformas
        """
        return self.db.query(PlatformDB).offset(skip).limit(limit).all()
    
    def get_enabled(self) -> List[PlatformDB]:
        """
        Busca todas as plataformas habilitadas
        
        Returns:
            Lista de plataformas habilitadas
        """
        return self.db.query(PlatformDB).filter(
            PlatformDB.enabled == True
        ).all()
    
    def update(self, platform_id: str, **kwargs) -> Optional[PlatformDB]:
        """
        Atualiza uma plataforma
        
        Args:
            platform_id: ID da plataforma
            **kwargs: Campos para atualizar
            
        Returns:
            PlatformDB atualizada ou None
        """
        platform = self.get_by_id(platform_id)
        if not platform:
            return None
        
        for key, value in kwargs.items():
            if hasattr(platform, key):
                setattr(platform, key, value)
        
        self.db.commit()
        self.db.refresh(platform)
        
        return platform
    
    def delete(self, platform_id: str) -> bool:
        """
        Remove uma plataforma
        
        Args:
            platform_id: ID da plataforma
            
        Returns:
            True se removido, False se não encontrado
        """
        platform = self.get_by_id(platform_id)
        if not platform:
            return False
        
        self.db.delete(platform)
        self.db.commit()
        
        return True