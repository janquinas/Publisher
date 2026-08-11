"""
Facebook Adapter - Publicação real de vídeos via Facebook Graph API

Fluxo de publicação em uma Page (3 etapas — Resumable Upload API):
  1. POST /{app_id}/uploads
       Parâmetros: file_name, file_length, file_type=video/mp4, access_token
       → Recebe { id: "upload:<upload_session_id>" }

  2. POST /{upload_session_id}
       Headers: Authorization: OAuth <token>, file_offset: 0
       Body: binário do arquivo
       → Recebe { h: "<file_handle>" }

  3. POST /{page_id}/videos
       Parâmetros: fbuploader_video_file_chunk=<file_handle>,
                   title, description, access_token
       → Recebe { id: "<video_id>" }

Autenticação:
  - credentials["access_token"] : Page Access Token com permissões
      pages_show_list, pages_read_engagement, pages_manage_posts
  - credentials["page_id"]      : ID da Página do Facebook onde publicar
      (retornado no OAuth callback e salvo no banco)

Referência:
  https://developers.facebook.com/docs/video-api/guides/publishing/
  https://developers.facebook.com/docs/video-api/guides/resumable-uploads/
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any

import requests

from ..models.result import Result
from ..models.media import Media
from .base_adapter import BasePlatformAdapter

_GRAPH_VERSION = "v21.0"
_GRAPH_URL     = f"https://graph.facebook.com/{_GRAPH_VERSION}"


class FacebookAdapter(BasePlatformAdapter):
    """Adaptador de publicação real para o Facebook via Graph API."""

    def __init__(self):
        super().__init__("facebook")

    # ------------------------------------------------------------------
    # Contrato da BasePlatformAdapter
    # ------------------------------------------------------------------

    def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        if not credentials.get("access_token"):
            self.log_warning("access_token ausente nas credenciais do Facebook")
            return False
        if not credentials.get("page_id"):
            self.log_warning(
                "page_id ausente. Reconecte a conta do Facebook em Conexões."
            )
            return False
        return True

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Valida o token consultando /me da Graph API."""
        if not self.validate_credentials(credentials):
            return False

        resp = requests.get(
            f"{_GRAPH_URL}/me",
            params={"access_token": credentials["access_token"], "fields": "id,name"},
            timeout=10,
        )
        if resp.status_code == 200 and "id" in resp.json():
            self.log_info("Autenticação com Facebook OK")
            return True

        err = resp.json().get("error", {}).get("message", resp.text[:150])
        self.log_error(f"Falha na autenticação com Facebook: {err}")
        return False

    def prepare_request(
        self,
        media: Media,
        title: str,
        description: str,
        credentials: Dict[str, str],
    ) -> Dict[str, Any]:
        """Monta os parâmetros para o POST final em /{page_id}/videos."""
        return {
            "title":        title[:255],
            "description":  (description or "")[:5000],
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
        Publica o vídeo na Página do Facebook.

        Fluxo:
          1. Iniciar sessão de upload.
          2. Enviar o arquivo binário.
          3. Publicar usando o file_handle recebido.
        """
        credentials = self._parse_credentials(credentials)

        try:
            self.log_info("Iniciando publicação no Facebook", title=title)

            if not self.authenticate(credentials):
                return Result(
                    platform_name="facebook",
                    success=False,
                    message="Falha na autenticação com Facebook. "
                            "Verifique se a conta está conectada em Conexões.",
                    error_code="AUTH_ERROR",
                )

            file_path = Path(media.file_path)
            if not file_path.exists():
                return Result(
                    platform_name="facebook",
                    success=False,
                    message=f"Arquivo de vídeo não encontrado: {media.file_path}",
                    error_code="FILE_NOT_FOUND",
                )

            access_token = credentials["access_token"]
            page_id      = credentials["page_id"]
            app_id       = os.getenv("FACEBOOK_APP_ID", "")
            file_size    = file_path.stat().st_size
            mime_type    = self._mime_type(file_path.suffix)

            if not app_id:
                return Result(
                    platform_name="facebook",
                    success=False,
                    message="FACEBOOK_APP_ID não configurado no .env.",
                    error_code="CONFIG_ERROR",
                )

            # 1. Iniciar sessão de upload
            session_resp = requests.post(
                f"{_GRAPH_URL}/{app_id}/uploads",
                params={
                    "file_name":   file_path.name,
                    "file_length": file_size,
                    "file_type":   mime_type,
                    "access_token": access_token,
                },
                timeout=30,
            )
            session_data = session_resp.json()

            if session_resp.status_code != 200 or "id" not in session_data:
                err = session_data.get("error", {}).get("message", session_resp.text[:200])
                self.log_error(f"Falha ao iniciar sessão de upload no Facebook: {err}")
                return Result(
                    platform_name="facebook",
                    success=False,
                    message=f"Falha ao iniciar upload: {err}",
                    error_code="UPLOAD_INIT_ERROR",
                )

            # session_id tem formato "upload:<id>"
            session_id = session_data["id"]
            self.log_info("Sessão de upload Facebook iniciada", session_id=session_id)

            # 2. Enviar arquivo
            file_handle = self._upload_file(session_id, file_path, access_token)
            if not file_handle:
                return Result(
                    platform_name="facebook",
                    success=False,
                    message="Falha ao enviar o vídeo para o Facebook.",
                    error_code="UPLOAD_ERROR",
                )

            # 3. Publicar na Página
            pub_params = self.prepare_request(media, title, description, credentials)
            pub_params["fbuploader_video_file_chunk"] = file_handle

            pub_resp = requests.post(
                f"https://graph-video.facebook.com/{_GRAPH_VERSION}/{page_id}/videos",
                data=pub_params,
                timeout=60,
            )
            pub_data = pub_resp.json()

            if pub_resp.status_code != 200 or "id" not in pub_data:
                err = pub_data.get("error", {}).get("message", pub_resp.text[:200])
                self.log_error(f"Falha ao publicar vídeo no Facebook: {err}")
                return Result(
                    platform_name="facebook",
                    success=False,
                    message=f"Falha ao publicar: {err}",
                    error_code="PUBLISH_ERROR",
                )

            video_id = pub_data["id"]
            post_url = f"https://www.facebook.com/watch/?v={video_id}"
            self.log_info("Vídeo publicado no Facebook", video_id=video_id)

            return Result(
                platform_name="facebook",
                success=True,
                message="Vídeo publicado com sucesso no Facebook",
                post_url=post_url,
                published_at=__import__("datetime").datetime.now(),
            )

        except requests.exceptions.ConnectionError:
            return Result(
                platform_name="facebook",
                success=False,
                message="Sem conexão com a internet ao publicar no Facebook.",
                error_code="CONNECTION_ERROR",
            )
        except requests.exceptions.Timeout:
            return Result(
                platform_name="facebook",
                success=False,
                message="Timeout ao publicar no Facebook. Tente novamente.",
                error_code="TIMEOUT_ERROR",
            )
        except Exception as e:
            self.log_error(f"Erro inesperado na publicação no Facebook: {e}")
            return Result(
                platform_name="facebook",
                success=False,
                message=f"Erro inesperado: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    def get_upload_url(self, credentials: Dict[str, str]) -> Optional[str]:
        page_id = credentials.get("page_id", "")
        return f"{_GRAPH_URL}/{page_id}/videos" if page_id else None

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

    def _upload_file(
        self,
        session_id: str,
        file_path: Path,
        access_token: str,
    ) -> Optional[str]:
        """
        Envia o arquivo binário para a sessão de upload do Facebook.
        Retorna o file_handle em caso de sucesso, None em caso de falha.
        Suporta retomada a partir do file_offset em caso de interrupção.
        """
        file_size   = file_path.stat().st_size
        file_offset = 0

        # Verificar se há upload parcial para retomar
        check_resp = requests.get(
            f"{_GRAPH_URL}/{session_id}",
            headers={"Authorization": f"OAuth {access_token}"},
            timeout=15,
        )
        if check_resp.status_code == 200:
            file_offset = int(check_resp.json().get("file_offset", 0))
            if file_offset > 0:
                self.log_info(
                    f"Retomando upload Facebook a partir do byte {file_offset}"
                )

        with open(file_path, "rb") as f:
            f.seek(file_offset)
            data = f.read()

        resp = requests.post(
            f"{_GRAPH_URL}/{session_id}",
            headers={
                "Authorization": f"OAuth {access_token}",
                "file_offset":   str(file_offset),
            },
            data=data,
            timeout=300,
        )
        resp_data = resp.json()

        if resp.status_code == 200 and "h" in resp_data:
            file_handle = resp_data["h"]
            self.log_info("Upload Facebook concluído", file_handle=file_handle[:20] + "...")
            return file_handle

        err = resp_data.get("debug_info", {}).get("message", resp.text[:200])
        self.log_error(f"Falha no upload Facebook: {err}")
        return None

    @staticmethod
    def _mime_type(extension: str) -> str:
        mapping = {
            ".mp4":  "video/mp4",
            ".mov":  "video/quicktime",
            ".webm": "video/webm",
        }
        return mapping.get(extension.lower(), "video/mp4")
