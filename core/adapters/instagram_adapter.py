"""
Instagram Adapter - Publicação real de vídeos/reels via Instagram Graph API

Fluxo de publicação de Reels (3 etapas):
  1. POST /{ig_id}/media
       Parâmetros: video_url (URL pública), media_type=REELS, caption, access_token
       → Recebe { id: <container_id> }

  2. POST rupload.facebook.com/ig-api-upload/{version}/{container_id}
       Headers: Authorization: OAuth <token>, offset: 0, file_size: <bytes>
       Body: binário do arquivo
       → Recebe { success: true } ou debug_info em caso de erro

     NOTA: Se o vídeo já estiver em uma URL pública acessível pela Meta,
     a etapa 2 pode ser substituída por video_url= na etapa 1 diretamente.
     O adapter usa a URL do endpoint de download do próprio backend.

  3. POST /{ig_id}/media_publish
       Parâmetros: creation_id=<container_id>, access_token
       → Recebe { id: <ig_media_id> }

Autenticação:
  - credentials["access_token"] : Page Access Token com permissões
      instagram_basic, instagram_content_publish, pages_read_engagement
  - credentials["ig_user_id"]   : Instagram Professional Account ID
      (retornado no OAuth callback e salvo no banco)
  - credentials["page_id"]      : Facebook Page ID vinculada à conta Instagram

Referência:
  https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/content-publishing/
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Any

import requests

from ..models.result import Result
from ..models.media import Media
from .base_adapter import BasePlatformAdapter

_GRAPH_VERSION    = "v21.0"
_GRAPH_URL        = f"https://graph.facebook.com/{_GRAPH_VERSION}"
_RUPLOAD_URL      = f"https://rupload.facebook.com/ig-api-upload/{_GRAPH_VERSION}"

# Tempo máximo de polling para o status do container (segundos)
_POLL_TIMEOUT  = 300   # 5 minutos
_POLL_INTERVAL = 10    # 10 segundos


class InstagramAdapter(BasePlatformAdapter):
    """Adaptador de publicação real para o Instagram via Graph API."""

    def __init__(self):
        super().__init__("instagram")

    # ------------------------------------------------------------------
    # Contrato da BasePlatformAdapter
    # ------------------------------------------------------------------

    def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        if not credentials.get("access_token"):
            self.log_warning("access_token ausente nas credenciais do Instagram")
            return False
        if not credentials.get("ig_user_id"):
            self.log_warning(
                "ig_user_id ausente. Reconecte a conta do Instagram em Conexões."
            )
            return False
        return True

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Valida o token consultando o endpoint /me da Graph API."""
        if not self.validate_credentials(credentials):
            return False

        resp = requests.get(
            f"{_GRAPH_URL}/me",
            params={"access_token": credentials["access_token"], "fields": "id,name"},
            timeout=10,
        )
        if resp.status_code == 200 and "id" in resp.json():
            self.log_info("Autenticação com Instagram OK")
            return True

        err = resp.json().get("error", {}).get("message", resp.text[:150])
        self.log_error(f"Falha na autenticação com Instagram: {err}")
        return False

    def prepare_request(
        self,
        media: Media,
        title: str,
        description: str,
        credentials: Dict[str, str],
    ) -> Dict[str, Any]:
        """Monta o payload do container de mídia."""
        caption = f"{title}\n\n{description}".strip() if description else title
        return {
            "media_type":   "REELS",
            "caption":      caption[:2200],    # limite do Instagram
            "access_token": credentials.get("access_token", ""),
        }

    def publish(
        self,
        media: Media,
        title: str,
        description: str,
        credentials: Dict[str, str],
    ) -> Result:
        """
        Publica o vídeo como Reel no Instagram.

        Fluxo:
          1. Criar container com video_url (URL pública do backend).
          2. Aguardar container ficar FINISHED.
          3. Publicar via media_publish.
        """
        credentials = self._parse_credentials(credentials)

        try:
            self.log_info("Iniciando publicação no Instagram", title=title)

            if not self.authenticate(credentials):
                return Result(
                    platform_name="instagram",
                    success=False,
                    message="Falha na autenticação com Instagram. "
                            "Verifique se a conta está conectada em Conexões.",
                    error_code="AUTH_ERROR",
                )

            ig_user_id = credentials["ig_user_id"]

            # URL pública do vídeo — o backend serve em /api/media/{id}/download
            video_url = self._public_video_url(media)
            if not video_url:
                return Result(
                    platform_name="instagram",
                    success=False,
                    message="Não foi possível gerar uma URL pública para o vídeo. "
                            "Configure BASE_URL no .env.",
                    error_code="URL_ERROR",
                )

            # 1. Criar container
            payload = self.prepare_request(media, title, description, credentials)
            payload["video_url"] = video_url

            resp = requests.post(
                f"{_GRAPH_URL}/{ig_user_id}/media",
                json=payload,
                timeout=30,
            )
            resp_data = resp.json()

            if resp.status_code != 200 or "id" not in resp_data:
                err = resp_data.get("error", {}).get("message", resp.text[:200])
                self.log_error(f"Falha ao criar container Instagram: {err}")
                return Result(
                    platform_name="instagram",
                    success=False,
                    message=f"Falha ao criar container: {err}",
                    error_code="CONTAINER_ERROR",
                )

            container_id = resp_data["id"]
            self.log_info("Container Instagram criado", container_id=container_id)

            # 2. Aguardar container ficar FINISHED
            status = self._poll_container_status(
                container_id, credentials["access_token"]
            )
            if status != "FINISHED":
                return Result(
                    platform_name="instagram",
                    success=False,
                    message=f"Container não ficou pronto para publicação (status: {status}). "
                            "Verifique se o vídeo atende aos requisitos do Instagram.",
                    error_code="CONTAINER_NOT_READY",
                )

            # 3. Publicar
            pub_resp = requests.post(
                f"{_GRAPH_URL}/{ig_user_id}/media_publish",
                json={
                    "creation_id":  container_id,
                    "access_token": credentials["access_token"],
                },
                timeout=30,
            )
            pub_data = pub_resp.json()

            if pub_resp.status_code != 200 or "id" not in pub_data:
                err = pub_data.get("error", {}).get("message", pub_resp.text[:200])
                self.log_error(f"Falha ao publicar no Instagram: {err}")
                return Result(
                    platform_name="instagram",
                    success=False,
                    message=f"Falha ao publicar: {err}",
                    error_code="PUBLISH_ERROR",
                )

            media_id  = pub_data["id"]
            post_url  = f"https://www.instagram.com/reel/{media_id}/"
            self.log_info("Reel publicado no Instagram", media_id=media_id)

            return Result(
                platform_name="instagram",
                success=True,
                message="Reel publicado com sucesso no Instagram",
                post_url=post_url,
                published_at=__import__("datetime").datetime.now(),
            )

        except requests.exceptions.ConnectionError:
            return Result(
                platform_name="instagram",
                success=False,
                message="Sem conexão com a internet ao publicar no Instagram.",
                error_code="CONNECTION_ERROR",
            )
        except requests.exceptions.Timeout:
            return Result(
                platform_name="instagram",
                success=False,
                message="Timeout ao publicar no Instagram. Tente novamente.",
                error_code="TIMEOUT_ERROR",
            )
        except Exception as e:
            self.log_error(f"Erro inesperado na publicação no Instagram: {e}")
            return Result(
                platform_name="instagram",
                success=False,
                message=f"Erro inesperado: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    def get_upload_url(self, credentials: Dict[str, str]) -> Optional[str]:
        ig_user_id = credentials.get("ig_user_id", "")
        return f"{_GRAPH_URL}/{ig_user_id}/media" if ig_user_id else None

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _parse_credentials(self, credentials) -> Dict[str, str]:
        if isinstance(credentials, str):
            try:
                return json.loads(credentials)
            except (json.JSONDecodeError, TypeError):
                return {}
        return dict(credentials) if credentials else {}

    def _public_video_url(self, media: Media) -> Optional[str]:
        """
        Gera a URL pública do vídeo usando BASE_URL do .env.
        O endpoint /api/media/{id}/download serve o arquivo diretamente.
        """
        base_url = os.getenv("BASE_URL", "").rstrip("/")
        if not base_url:
            # Fallback: tentar construir a partir de FRONTEND_URL
            frontend = os.getenv("FRONTEND_URL", "")
            if frontend:
                from urllib.parse import urlparse
                parsed   = urlparse(frontend)
                base_url = f"{parsed.scheme}://{parsed.netloc}"

        if not base_url:
            return None

        media_id = getattr(media, "id", None) or getattr(media, "publication_id", None)
        if not media_id:
            return None

        return f"{base_url}/api/media/{media_id}/download"

    def _poll_container_status(
        self,
        container_id: str,
        access_token: str,
    ) -> str:
        """
        Consulta o status do container a cada _POLL_INTERVAL segundos
        até ficar FINISHED, ERROR ou expirar o timeout.
        Retorna o status final.
        """
        elapsed = 0
        while elapsed < _POLL_TIMEOUT:
            resp = requests.get(
                f"{_GRAPH_URL}/{container_id}",
                params={
                    "fields":       "status_code",
                    "access_token": access_token,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                status = resp.json().get("status_code", "UNKNOWN")
                self.log_info(
                    f"Status do container Instagram: {status} ({elapsed}s decorridos)"
                )
                if status in ("FINISHED", "ERROR", "EXPIRED"):
                    return status
            time.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL

        self.log_warning("Timeout aguardando container Instagram ficar FINISHED")
        return "TIMEOUT"
