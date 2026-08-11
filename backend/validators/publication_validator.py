"""
Publication Validator - Validação de dados de publicação
"""
from typing import List
from datetime import datetime


class PublicationValidator:
    """Validador de dados de publicação"""
    
    @staticmethod
    def validate_title(title: str) -> bool:
        if not title or not title.strip():
            raise ValueError("Título é obrigatório")

        if len(title) > 300:
            raise ValueError("Título deve ter no máximo 300 caracteres")

        return True
    
    @staticmethod
    def validate_description(description: str) -> bool:
        """
        Valida descrição da publicação.
        Descrição vazia é aceita — o campo é opcional no fluxo de agendamento.

        Args:
            description: Descrição a ser validada

        Returns:
            bool: True se válido

        Raises:
            ValueError: Se descrição inválida
        """
        if description is None:
            return True

        if len(description) > 5000:
            raise ValueError("Descrição deve ter no máximo 5000 caracteres")

        return True
    
    @staticmethod
    def validate_platforms(platforms: List[str]) -> bool:
        """
        Valida lista de plataformas
        
        Args:
            platforms: Lista de plataformas
            
        Returns:
            bool: True se válido
            
        Raises:
            ValueError: Se plataformas inválidas
        """
        if not platforms or len(platforms) == 0:
            raise ValueError("Pelo menos uma plataforma deve ser selecionada")
        
        allowed_platforms = ["youtube", "instagram", "tiktok", "facebook", "kwai"]
        
        for platform in platforms:
            if platform.lower() not in allowed_platforms:
                raise ValueError(
                    f"Plataforma inválida: {platform}. "
                    f"Plataformas permitidas: {', '.join(allowed_platforms)}"
                )
        
        return True
    
    @staticmethod
    def validate_scheduled_at(scheduled_at: datetime) -> bool:
        """
        Valida data/hora de agendamento
        
        Args:
            scheduled_at: Data/hora a ser validada
            
        Returns:
            bool: True se válido
            
        Raises:
            ValueError: Se data/hora inválida
        """
        if not scheduled_at:
            raise ValueError("Data/hora de agendamento é obrigatória")
        
        # Verificar se é no futuro
        if scheduled_at <= datetime.utcnow():
            raise ValueError("Data/hora de agendamento deve ser no futuro")
        
        return True
    
    @staticmethod
    def validate_publication_data(title: str, description: str, platforms: List[str],
                                  scheduled_at: datetime = None) -> dict:
        """
        Valida todos os dados de publicação
        
        Args:
            title: Título
            description: Descrição
            platforms: Lista de plataformas
            scheduled_at: Data/hora de agendamento (opcional)
            
        Returns:
            Dict com dados validados
            
        Raises:
            ValueError: Se algum dado for inválido
        """
        # Validar cada campo
        PublicationValidator.validate_title(title)
        PublicationValidator.validate_description(description)
        PublicationValidator.validate_platforms(platforms)
        
        if scheduled_at:
            PublicationValidator.validate_scheduled_at(scheduled_at)
        
        return {
            "title": title.strip(),
            "description": (description or "").strip(),
            "platforms": [p.lower() for p in platforms],
            "scheduled_at": scheduled_at
        }