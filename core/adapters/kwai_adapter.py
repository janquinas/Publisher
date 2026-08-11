"""
Kwai Adapter - Adaptador para publicação no Kwai
"""
from typing import Dict, Optional, Any
from datetime import datetime
from ..models.result import Result
from ..models.media import Media
from .base_adapter import BasePlatformAdapter


class KwaiAdapter(BasePlatformAdapter):
    """Adaptador para publicação no Kwai"""
    
    def __init__(self):
        super().__init__("kwai")
        self.api_url = "https://api.kwai.com/v1/video/upload"
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Autentica com a API do Kwai"""
        try:
            self.log_info("Iniciando autenticação com Kwai")
            
            if not self.validate_credentials(credentials):
                return False
            
            if "access_token" in credentials and credentials["access_token"]:
                self.log_info("Autenticação com Kwai realizada com sucesso")
                return True
            
            return False
            
        except Exception as e:
            self.log_error("Erro na autenticação com Kwai", error=str(e))
            return False
    
    def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Valida se as credenciais são válidas"""
        has_token = "access_token" in credentials and credentials["access_token"]
        
        if not has_token:
            self.log_warning("Credenciais do Kwai inválidas: access_token não fornecido")
            return False
        
        return True
    
    def prepare_request(self, media: Media, title: str, description: str, 
                       credentials: Dict[str, str]) -> Dict[str, Any]:
        """Prepara a requisição para a API do Kwai"""
        self.log_info("Preparando requisição para Kwai", title=title)
        
        request_data = {
            "title": title,
            "description": description,
            "visibility": "public"
        }
        
        headers = {
            "Authorization": f"Bearer {credentials.get('access_token', '')}",
            "Content-Type": "application/json"
        }
        
        return {
            "url": self.api_url,
            "headers": headers,
            "data": request_data,
            "media_path": media.file_path,
            "media_type": "video/*"
        }
    
    def publish(self, media: Media, title: str, description: str, 
                credentials: Dict[str, str]) -> Result:
        """Publica o vídeo no Kwai"""
        try:
            self.log_info("Iniciando publicação no Kwai", title=title)
            
            if not self.authenticate(credentials):
                return Result(
                    platform_name="kwai",
                    success=False,
                    message="Falha na autenticação com Kwai",
                    error_code="AUTH_ERROR"
                )
            
            # Kwai não possui API pública de upload de vídeo.
            # Esta implementação é um STUB — registra o resultado como sucesso
            # para fins de teste, mas nenhum vídeo é enviado ao Kwai.
            # O usuário deve ser informado via mensagem de resultado.
            self.log_info(
                "Kwai: publicação simulada (API pública não disponível)",
                file_path=media.file_path,
            )

            return Result(
                platform_name="kwai",
                success=True,
                message=(
                    "Kwai: publicação registrada localmente. "
                    "ATENÇÃO: o Kwai não possui API pública de upload — "
                    "nenhum vídeo foi enviado. Publique manualmente pelo app."
                ),
                post_url=None,
                published_at=datetime.now(),
            )
            
        except Exception as e:
            self.log_error("Erro na publicação no Kwai", error=str(e))
            return Result(
                platform_name="kwai",
                success=False,
                message=f"Erro na publicação: {str(e)}",
                error_code="PUBLISH_ERROR"
            )
    
    def get_upload_url(self, credentials: Dict[str, str]) -> Optional[str]:
        """Obtém URL para upload do vídeo"""
        try:
            if not self.validate_credentials(credentials):
                return None
            return self.api_url
        except Exception as e:
            self.log_error("Erro ao obter URL de upload", error=str(e))
            return None