"""
Request Mapper - Converte dados HTTP para modelos internos do núcleo
"""
from typing import Dict, Any
from datetime import datetime
from core.models.publication import Publication
from core.models.platform import Platform
from core.models.media import Media
from core.models.schedule import Schedule


class RequestMapper:
    """Mapper para converter requisições HTTP em modelos do núcleo"""
    
    @staticmethod
    def to_publication_model(
        title: str,
        description: str,
        platforms: list,
        media_path: str = None,
        media_size_mb: float = None,
        media_format: str = None,
        scheduled_at: datetime = None
    ) -> Publication:
        """
        Converte dados de requisição para modelo Publication
        
        Args:
            title: Título da publicação
            description: Descrição
            platforms: Lista de nomes de plataformas
            media_path: Caminho do arquivo de mídia
            media_size_mb: Tamanho do arquivo em MB
            media_format: Formato do arquivo
            scheduled_at: Data/hora de agendamento
            
        Returns:
            Publication: Modelo de publicação do núcleo
        """
        # Criar objeto Media se fornecido
        media = None
        if media_path:
            media = Media(
                file_path=media_path,
                file_size_mb=media_size_mb or 0.0,
                format=media_format or "mp4"
            )
        
        # Criar objetos Platform
        platform_objects = []
        for platform_name in platforms:
            platform = Platform(
                name=platform_name.lower(),
                credentials={},
                enabled=True
            )
            platform_objects.append(platform)
        
        # Criar objeto Schedule se fornecido
        schedule = None
        if scheduled_at:
            schedule = Schedule(
                scheduled_at=scheduled_at,
                status="pending"
            )
        
        # Criar publicação
        publication = Publication(
            title=title,
            description=description,
            media=media,
            platforms=platform_objects,
            schedule=schedule
        )
        
        return publication
    
    @staticmethod
    def from_multipart_form_data(
        form_data: Dict[str, Any],
        file_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Converte dados de formulário multipart para dicionário
        
        Args:
            form_data: Dados do formulário
            file_data: Dados do arquivo (opcional)
            
        Returns:
            Dict com dados convertidos
        """
        # Extrair campos básicos
        title = form_data.get("title", "").strip()
        description = form_data.get("description", "").strip()
        
        # Extrair plataformas (podem vir como string separada por vírgulas ou lista)
        platforms_raw = form_data.get("platforms", "")
        if isinstance(platforms_raw, str):
            platforms = [p.strip().lower() for p in platforms_raw.split(",") if p.strip()]
        else:
            platforms = [p.lower() for p in platforms_raw]
        
        # Extrair data/hora de agendamento
        scheduled_at = None
        scheduled_at_str = form_data.get("scheduled_at")
        if scheduled_at_str:
            try:
                scheduled_at = datetime.fromisoformat(scheduled_at_str)
            except ValueError:
                pass
        
        # Extrair dados do arquivo
        media_path = None
        media_size_mb = None
        media_format = None
        
        if file_data and "file" in file_data:
            file_obj = file_data["file"]
            media_path = file_obj.filename
            # UploadFile.size pode ser None antes de ler o conteúdo do arquivo
            raw_size = getattr(file_obj, "size", None)
            media_size_mb = raw_size / (1024 * 1024) if raw_size else None
            
            # Obter extensão
            _, ext = media_path.rsplit(".", 1) if "." in media_path else ("", "")
            media_format = f".{ext.lower()}" if ext else "mp4"
        
        return {
            "title": title,
            "description": description,
            "platforms": platforms,
            "media_path": media_path,
            "media_size_mb": media_size_mb,
            "media_format": media_format,
            "scheduled_at": scheduled_at
        }
