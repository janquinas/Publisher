"""
Media Manager - Gerenciamento de arquivos de mídia
"""
import os
from typing import Optional, Dict, Any
from ..models.media import Media
from ..config import ALLOWED_VIDEO_EXTENSIONS, MAX_VIDEO_SIZE_MB
from .log_manager import get_log_manager


class MediaManager:
    """Gerenciador de arquivos de mídia do núcleo"""
    
    def __init__(self):
        self.logger = get_log_manager("core.media_manager")
        self.registered_media: Dict[str, Media] = {}
    
    def register_media(self, file_path: str, file_size_mb: float, format: str, 
                       duration_seconds: Optional[int] = None, 
                       thumbnail_path: Optional[str] = None) -> Media:
        """
        Registra um arquivo de mídia no sistema
        
        Args:
            file_path: Caminho do arquivo de vídeo
            file_size_mb: Tamanho do arquivo em MB
            format: Formato do arquivo
            duration_seconds: Duração em segundos (opcional)
            thumbnail_path: Caminho da thumbnail (opcional)
            
        Returns:
            Media: Objeto Media validado
            
        Raises:
            ValueError: Se o arquivo for inválido
        """
        self.logger.info(
            "Registrando arquivo de mídia",
            file_path=file_path,
            format=format,
            file_size_mb=file_size_mb
        )
        
        # Validar formato (garantir que tem o ponto)
        format_normalized = format.lower() if format.startswith('.') else f".{format.lower()}"
        if format_normalized not in ALLOWED_VIDEO_EXTENSIONS:
            raise ValueError(
                f"Formato de vídeo não suportado: {format}. "
                f"Formatos permitidos: {ALLOWED_VIDEO_EXTENSIONS}"
            )
        
        # Validar tamanho
        if file_size_mb > MAX_VIDEO_SIZE_MB:
            raise ValueError(
                f"Arquivo muito grande: {file_size_mb}MB. "
                f"Tamanho máximo permitido: {MAX_VIDEO_SIZE_MB}MB"
            )
        
        # Validar se arquivo existe
        if not os.path.exists(file_path):
            raise ValueError(f"Arquivo não encontrado: {file_path}")
        
        # Criar objeto Media
        media = Media(
            file_path=file_path,
            file_size_mb=file_size_mb,
            format=format.lower(),
            duration_seconds=duration_seconds,
            thumbnail_path=thumbnail_path
        )
        
        # Registrar no dicionário
        self.registered_media[file_path] = media
        
        self.logger.info(
            "Arquivo de mídia registrado com sucesso",
            file_path=file_path,
            format=media.format,
            file_size_mb=media.file_size_mb
        )
        
        return media
    
    def get_media(self, file_path: str) -> Optional[Media]:
        """
        Recupera um arquivo de mídia registrado
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Media ou None se não encontrado
        """
        return self.registered_media.get(file_path)
    
    def validate_media(self, media: Media) -> bool:
        """
        Valida se um arquivo de mídia está válido para publicação
        
        Args:
            media: Objeto Media a ser validado
            
        Returns:
            bool: True se válido, False caso contrário
        """
        # Validar formato
        if media.format.lower() not in ALLOWED_VIDEO_EXTENSIONS:
            self.logger.warning(
                "Formato de vídeo inválido",
                format=media.format,
                allowed=ALLOWED_VIDEO_EXTENSIONS
            )
            return False
        
        # Validar tamanho
        if media.file_size_mb > MAX_VIDEO_SIZE_MB:
            self.logger.warning(
                "Arquivo muito grande",
                file_size_mb=media.file_size_mb,
                max_size_mb=MAX_VIDEO_SIZE_MB
            )
            return False
        
        # Validar se arquivo existe
        if not os.path.exists(media.file_path):
            self.logger.warning(
                "Arquivo não encontrado",
                file_path=media.file_path
            )
            return False
        
        return True
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtém informações de um arquivo de mídia
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dict com informações do arquivo ou dict vazio se não encontrado
        """
        media = self.get_media(file_path)
        if not media:
            return {}
        
        return {
            "file_path": media.file_path,
            "file_size_mb": media.file_size_mb,
            "format": media.format,
            "duration_seconds": media.duration_seconds,
            "thumbnail_path": media.thumbnail_path
        }
    
    def remove_media(self, file_path: str) -> bool:
        """
        Remove um arquivo de mídia do registro
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            bool: True se removido, False se não existia
        """
        if file_path in self.registered_media:
            del self.registered_media[file_path]
            self.logger.info("Arquivo de mídia removido do registro", file_path=file_path)
            return True
        return False
    
    def list_registered_media(self) -> list:
        """
        Lista todos os arquivos de mídia registrados
        
        Returns:
            Lista de caminhos de arquivos registrados
        """
        return list(self.registered_media.keys())
    
    def clear_registry(self):
        """Limpa todos os registros de mídia"""
        self.registered_media.clear()
        self.logger.info("Registro de mídia limpo")
