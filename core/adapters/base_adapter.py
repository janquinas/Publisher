"""
Base Adapter - Interface base para todos os adaptadores de plataforma
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from ..models.result import Result
from ..models.media import Media


class BasePlatformAdapter(ABC):
    """Interface base para adaptadores de plataforma"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = None  # Será injetado pelo LogManager
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Autentica com a plataforma
        
        Args:
            credentials: Dicionário com credenciais (api_key, access_token, etc.)
            
        Returns:
            bool: True se autenticado com sucesso
        """
        pass
    
    @abstractmethod
    def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """
        Valida se as credenciais são válidas
        
        Args:
            credentials: Dicionário com credenciais
            
        Returns:
            bool: True se credenciais válidas
        """
        pass
    
    @abstractmethod
    def prepare_request(self, media: Media, title: str, description: str, 
                       credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Prepara a requisição para a API da plataforma
        
        Args:
            media: Objeto Media com informações do arquivo
            title: Título da publicação
            description: Descrição da publicação
            credentials: Credenciais de autenticação
            
        Returns:
            Dict com dados da requisição preparada
        """
        pass
    
    @abstractmethod
    def publish(self, media: Media, title: str, description: str, 
                credentials: Dict[str, str]) -> Result:
        """
        Publica o vídeo na plataforma
        
        Args:
            media: Objeto Media com informações do arquivo
            title: Título da publicação
            description: Descrição da publicação
            credentials: Credenciais de autenticação
            
        Returns:
            Result: Resultado da publicação
        """
        pass
    
    @abstractmethod
    def get_upload_url(self, credentials: Dict[str, str]) -> Optional[str]:
        """
        Obtém URL para upload do vídeo
        
        Args:
            credentials: Credenciais de autenticação
            
        Returns:
            URL de upload ou None se houver erro
        """
        pass
    
    def set_logger(self, logger):
        """Injeta logger no adaptador"""
        self.logger = logger
    
    def log_info(self, message: str, **kwargs):
        """Registra mensagem de informação"""
        if self.logger:
            if kwargs:
                self.logger.info(f"[{self.platform_name}] {message} | {kwargs}")
            else:
                self.logger.info(f"[{self.platform_name}] {message}")
    
    def log_error(self, message: str, **kwargs):
        """Registra mensagem de erro"""
        if self.logger:
            if kwargs:
                self.logger.error(f"[{self.platform_name}] {message} | {kwargs}")
            else:
                self.logger.error(f"[{self.platform_name}] {message}")
    
    def log_warning(self, message: str, **kwargs):
        """Registra mensagem de aviso"""
        if self.logger:
            if kwargs:
                self.logger.warning(f"[{self.platform_name}] {message} | {kwargs}")
            else:
                self.logger.warning(f"[{self.platform_name}] {message}")
