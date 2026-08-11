"""
Response Mapper - Converte resultados do núcleo para respostas HTTP
"""
from typing import Dict, Any, List
from datetime import datetime
from core.models.result import Result
from core.models.publication import Publication


class ResponseMapper:
    """Mapper para converter modelos do núcleo em respostas HTTP"""
    
    @staticmethod
    def to_publication_response(publication) -> Dict[str, Any]:
        """
        Converte modelo Publication para resposta HTTP.
        Aceita tanto objetos Publication (Pydantic) quanto PublicationDB (SQLAlchemy).
        """
        import json as _json
        pub_id = str(publication.id) if publication.id else ""

        # Resolve platforms: from DB column (JSON string) or from in-memory list
        platforms: list = []
        raw = getattr(publication, "platforms", None)
        if raw:
            if isinstance(raw, str):
                # DB column: stored as JSON string '["instagram","tiktok"]'
                try:
                    parsed = _json.loads(raw)
                    if isinstance(parsed, list):
                        platforms = [str(p) for p in parsed]
                except Exception:
                    pass
            elif isinstance(raw, list):
                # In-memory Pydantic list — may contain Platform objects or strings
                if len(raw) > 0:
                    if hasattr(raw[0], "name"):
                        platforms = [p.name for p in raw]
                    else:
                        platforms = [str(p) for p in raw]

        schedule = getattr(publication, "schedule", None)
        # Also check the DB relationship (SQLAlchemy)
        if not schedule:
            schedules_rel = getattr(publication, "schedules", None)
            if schedules_rel:
                schedule = schedules_rel[0] if len(schedules_rel) > 0 else None

        status_val = "pending"
        scheduled_at_val = None
        if schedule:
            status_val = getattr(schedule, "status", "scheduled") or "scheduled"
            scheduled_at_val = getattr(schedule, "scheduled_at", None)

        created_at = getattr(publication, "created_at", None)
        updated_at = getattr(publication, "updated_at", None)
        now = datetime.utcnow().isoformat()

        return {
            "id": pub_id,
            "title": publication.title,
            "description": publication.description,
            "platforms": platforms,
            "status": status_val,
            "scheduled_at": scheduled_at_val.isoformat() if scheduled_at_val else None,
            "created_at": created_at.isoformat() if created_at else now,
            "updated_at": updated_at.isoformat() if updated_at else now,
        }
    
    @staticmethod
    def to_publication_list_response(publications: List[Publication], total: int) -> Dict[str, Any]:
        """
        Converte lista de publicações para resposta HTTP
        
        Args:
            publications: Lista de publicações
            total: Total de publicações
            
        Returns:
            Dict com lista formatada
        """
        return {
            "publications": [
                ResponseMapper.to_publication_response(pub) 
                for pub in publications
            ],
            "total": total
        }
    
    @staticmethod
    def to_result_response(result: Result) -> Dict[str, Any]:
        """
        Converte modelo Result para resposta HTTP
        
        Args:
            result: Modelo de resultado do núcleo
            
        Returns:
            Dict com dados formatados para resposta
        """
        return {
            "platform": result.platform_name,
            "success": result.success,
            "message": result.message,
            "post_url": result.post_url,
            "error_code": result.error_code,
            "published_at": result.published_at.isoformat() if result.published_at else None
        }
    
    @staticmethod
    def to_error_response(
        message: str,
        status_code: int = 400,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Cria resposta de erro padronizada
        
        Args:
            message: Mensagem de erro
            status_code: Código HTTP
            details: Detalhes adicionais
            
        Returns:
            Dict com resposta de erro
        """
        response = {
            "error": True,
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if details:
            response["details"] = details
        
        return response
    
    @staticmethod
    def to_success_response(
        message: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Cria resposta de sucesso padronizada
        
        Args:
            message: Mensagem de sucesso
            data: Dados adicionais
            
        Returns:
            Dict com resposta de sucesso
        """
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if data:
            response["data"] = data
        
        return response