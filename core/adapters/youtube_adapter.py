"""
YouTube Adapter - Publicação real de vídeos via YouTube Data API v3

Fluxo de upload resumidão (Resumable Upload):
  1. POST https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable
     → recebe um upload URI na resposta
  2. PUT <upload_uri> com o binário do vídeo
     → recebe o recurso Video com o videoId

Autenticação:
  - credentials["access_token"]  : token OAuth 2.0 do usuário
  - credentials["refresh_token"] : token de renovação (salvo no OAuth callback)
  O adapter renova automaticamente o access_token quando recebe 401.

Referência:
  https://developers.google.com/youtube/v3/guides/uploading_a_video
"""
from __future__ import annotations

import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Any

import requests

from ..models.result import Result
from ..models.media import Media
from .base_adapter import BasePlatformAdapter

# Tamanho de cada chunk no upload resumível (256 KB múltiplo — mínimo recomendado: 5 MB)
_CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB

# URL base da YouTube Data API v3
_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
_TOKEN_URL  = "https://oauth2.googleapis.com/token"

# Categorias do YouTube (padrão: 22 = People & Blogs)
_DEFAULT_CATEGORY = "22"

_log = logging.getLogger("core.adapters.youtube")


class YouTubeAdapter(BasePlatformAdapter):
    """Adaptador de publicação real para o YouTube via Data API v3."""

    def __init__(self):
        super().__init__("youtube")

    # ------------------------------------------------------------------
    # Contrato da BasePlatformAdapter
    # ------------------------------------------------------------------

    def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Verifica se existe pelo menos um access_token não vazio."""
        token = credentials.get("access_token", "")
        if not token:
            self.log_warning("access_token ausente nas credenciais do YouTube")
            return False
        return True

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Testa o token fazendo uma requisição leve à API.
        Se receber 401, tenta renovar via refresh_token.
        Retorna True se autenticado com sucesso.
        """
        if not self.validate_credentials(credentials):
            return False

        url = "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true"
        resp = requests.get(url, headers=self._auth_headers(credentials), timeout=10)

        if resp.status_code == 401:
            self.log_info("access_token expirado, tentando renovar...")
            new_token = self._refresh_access_token(credentials)
            if not new_token:
                self.log_error("Falha ao renovar access_token")
                return False
            credentials["access_token"] = new_token
            resp = requests.get(url, headers=self._auth_headers(credentials), timeout=10)

        if resp.status_code == 200:
            self.log_info("Autenticação com YouTube OK")
            return True

        self.log_error(f"Falha na autenticação: {resp.status_code} {resp.text[:200]}")
        return False

    def prepare_request(
        self,
        media: Media,
        title: str,
        description: str,
        credentials: Dict[str, str],
    ) -> Dict[str, Any]:
        """Monta o payload de metadados para o upload resumível."""
        return {
            "snippet": {
                "title": title[:100],             # limite da API: 100 chars
                "description": (description or "")[:5000],
                "tags": ["autopublished"],
                "categoryId": credentials.get("category_id", _DEFAULT_CATEGORY),
            },
            "status": {
                "privacyStatus": credentials.get("privacy_status", "public"),
                "selfDeclaredMadeForKids": False,
            },
        }

    def publish(
        self,
        media: Media,
        title: str,
        description: str,
        credentials: Dict[str, str],
    ) -> Result:
        """
        Faz o upload real do vídeo para o YouTube.

        Fluxo:
          1. Tenta autenticar (renova token se necessário).
          2. Inicia upload resumível → obtém upload_uri.
          3. Envia o arquivo em chunks.
          4. Retorna Result com o videoId e a URL pública.
        """
        # Garantir que credentials é dict (vem como str do banco)
        credentials = self._parse_credentials(credentials)

        try:
            self.log_info("Iniciando publicação no YouTube", title=title)

            # 1. Autenticar
            if not self.authenticate(credentials):
                return Result(
                    platform_name="youtube",
                    success=False,
                    message="Falha na autenticação com YouTube. "
                            "Verifique se a conta está conectada em Conexões.",
                    error_code="AUTH_ERROR",
                )

            # 2. Verificar arquivo
            file_path = Path(media.file_path)
            if not file_path.exists():
                return Result(
                    platform_name="youtube",
                    success=False,
                    message=f"Arquivo de vídeo não encontrado: {media.file_path}",
                    error_code="FILE_NOT_FOUND",
                )

            # 3. Iniciar upload resumível
            metadata = self.prepare_request(media, title, description, credentials)
            upload_uri = self._initiate_resumable_upload(
                credentials=credentials,
                metadata=metadata,
                file_size=file_path.stat().st_size,
                mime_type=self._mime_type(file_path.suffix),
            )
            if not upload_uri:
                return Result(
                    platform_name="youtube",
                    success=False,
                    message="Falha ao iniciar upload resumível no YouTube.",
                    error_code="UPLOAD_INIT_ERROR",
                )

            # 4. Enviar arquivo em chunks
            video_id = self._upload_file(upload_uri, file_path)
            if not video_id:
                return Result(
                    platform_name="youtube",
                    success=False,
                    message="Falha ao enviar o vídeo para o YouTube.",
                    error_code="UPLOAD_ERROR",
                )

            post_url = f"https://www.youtube.com/watch?v={video_id}"
            self.log_info("Vídeo publicado com sucesso no YouTube", video_id=video_id)

            return Result(
                platform_name="youtube",
                success=True,
                message="Vídeo publicado com sucesso no YouTube",
                post_url=post_url,
                published_at=__import__("datetime").datetime.now(),
            )

        except requests.exceptions.ConnectionError:
            return Result(
                platform_name="youtube",
                success=False,
                message="Sem conexão com a internet ao tentar publicar no YouTube.",
                error_code="CONNECTION_ERROR",
            )
        except requests.exceptions.Timeout:
            return Result(
                platform_name="youtube",
                success=False,
                message="Timeout ao publicar no YouTube. Tente novamente.",
                error_code="TIMEOUT_ERROR",
            )
        except Exception as e:
            self.log_error("Erro inesperado na publicação no YouTube", error=str(e))
            return Result(
                platform_name="youtube",
                success=False,
                message=f"Erro inesperado: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    def get_upload_url(self, credentials: Dict[str, str]) -> Optional[str]:
        """Retorna a URL base de upload (usada em testes de conectividade)."""
        return _UPLOAD_URL

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _auth_headers(self, credentials: Dict[str, str]) -> Dict[str, str]:
        return {"Authorization": f"Bearer {credentials.get('access_token', '')}"}

    def _parse_credentials(self, credentials) -> Dict[str, str]:
        """
        Garante que credentials é um dict.
        O platform_repository salva as credenciais como JSON string no banco.
        """
        if isinstance(credentials, str):
            try:
                return json.loads(credentials)
            except (json.JSONDecodeError, TypeError):
                return {}
        if credentials is None:
            return {}
        return dict(credentials)

    def _refresh_access_token(self, credentials: Dict[str, str]) -> Optional[str]:
        """
        Usa o refresh_token para obter um novo access_token via Google OAuth.
        Retorna o novo access_token ou None em caso de falha.
        """
        refresh_token = credentials.get("refresh_token", "")
        if not refresh_token:
            self.log_warning("refresh_token ausente — não é possível renovar o token")
            return None

        client_id     = os.getenv("YOUTUBE_CLIENT_ID", "")
        client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            self.log_error(
                "YOUTUBE_CLIENT_ID ou YOUTUBE_CLIENT_SECRET não configurados no .env"
            )
            return None

        try:
            resp = requests.post(
                _TOKEN_URL,
                data={
                    "client_id":     client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type":    "refresh_token",
                },
                timeout=15,
            )
            data = resp.json()
            new_token = data.get("access_token")
            if new_token:
                self.log_info("access_token renovado com sucesso")
                # Persistir token renovado no banco (best-effort)
                self._persist_new_token(new_token, credentials)
            else:
                self.log_error(
                    f"Resposta inesperada ao renovar token: {data}"
                )
            return new_token
        except Exception as e:
            self.log_error(f"Erro ao renovar access_token: {e}")
            return None

    def _persist_new_token(self, new_token: str, credentials: Dict[str, str]):
        """
        Atualiza o access_token no banco de dados (best-effort, falha silenciosa).
        Usa uma sessão própria para não interferir na sessão da request atual.
        """
        try:
            from core.database.config import SessionLocal
            from core.database.repositories.platform_repository import PlatformRepository

            credentials["access_token"] = new_token
            db = SessionLocal()
            try:
                repo = PlatformRepository(db)
                platform = repo.get_by_name("youtube")
                if platform:
                    repo.update(str(platform.id), credentials=json.dumps(credentials))
            finally:
                db.close()
        except Exception as e:
            self.log_warning(f"Não foi possível persistir o token renovado: {e}")

    def _initiate_resumable_upload(
        self,
        credentials: Dict[str, str],
        metadata: Dict[str, Any],
        file_size: int,
        mime_type: str,
    ) -> Optional[str]:
        """
        Etapa 1 do upload resumível: registra o upload e obtém o upload URI.

        Referência:
          https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol
        """
        params = {
            "uploadType": "resumable",
            "part":       "snippet,status",
        }
        headers = {
            **self._auth_headers(credentials),
            "Content-Type":           "application/json; charset=UTF-8",
            "X-Upload-Content-Type":  mime_type,
            "X-Upload-Content-Length": str(file_size),
        }

        resp = requests.post(
            _UPLOAD_URL,
            params=params,
            headers=headers,
            json=metadata,
            timeout=30,
        )

        if resp.status_code not in (200, 201):
            self.log_error(
                f"Falha ao iniciar upload resumível: {resp.status_code} {resp.text[:300]}"
            )
            return None

        upload_uri = resp.headers.get("Location")
        if not upload_uri:
            self.log_error("Upload URI não retornado pelo YouTube")
            return None

        self.log_info("Upload resumível iniciado", upload_uri=upload_uri[:60] + "...")
        return upload_uri

    def _upload_file(self, upload_uri: str, file_path: Path) -> Optional[str]:
        """
        Etapa 2 do upload resumível: envia o arquivo em chunks.
        Retorna o videoId em caso de sucesso, None em caso de falha.
        """
        file_size   = file_path.stat().st_size
        uploaded    = 0
        max_retries = 3

        with open(file_path, "rb") as f:
            while uploaded < file_size:
                chunk = f.read(_CHUNK_SIZE)
                if not chunk:
                    break

                chunk_end = uploaded + len(chunk) - 1
                headers   = {
                    "Content-Length": str(len(chunk)),
                    "Content-Range":  f"bytes {uploaded}-{chunk_end}/{file_size}",
                }

                # Retries com backoff exponencial
                attempt = 0
                while attempt < max_retries:
                    resp = requests.put(
                        upload_uri,
                        headers=headers,
                        data=chunk,
                        timeout=120,
                    )

                    # Upload completo — YouTube retorna 200 ou 201 com o recurso Video
                    if resp.status_code in (200, 201):
                        video_data = resp.json()
                        video_id   = video_data.get("id")
                        self.log_info(
                            f"Upload concluído: {uploaded + len(chunk)}/{file_size} bytes",
                            video_id=video_id,
                        )
                        return video_id

                    # Chunk aceito — continuar com o próximo
                    if resp.status_code == 308:
                        range_header = resp.headers.get("Range", "")
                        if range_header:
                            # Range: bytes=0-<last_byte_received>
                            uploaded = int(range_header.split("-")[1]) + 1
                        else:
                            uploaded += len(chunk)
                        self.log_info(
                            f"Progresso: {uploaded}/{file_size} bytes "
                            f"({100 * uploaded // file_size}%)"
                        )
                        break  # sair do loop de retry e pegar próximo chunk

                    # Erro recuperável (5xx) — retry com backoff
                    if resp.status_code >= 500:
                        attempt += 1
                        wait = 2 ** attempt
                        self.log_warning(
                            f"Erro {resp.status_code} no upload, tentativa {attempt}/{max_retries}. "
                            f"Aguardando {wait}s..."
                        )
                        time.sleep(wait)
                        continue

                    # Erro não recuperável (4xx)
                    self.log_error(
                        f"Erro fatal no upload: {resp.status_code} {resp.text[:200]}"
                    )
                    return None

                else:
                    # Esgotou retries
                    self.log_error("Upload falhou após máximo de tentativas")
                    return None

        self.log_error("Upload encerrou sem receber videoId")
        return None

    @staticmethod
    def _mime_type(extension: str) -> str:
        """Mapeia extensão de arquivo para MIME type."""
        mapping = {
            ".mp4":  "video/mp4",
            ".mov":  "video/quicktime",
            ".avi":  "video/x-msvideo",
            ".mkv":  "video/x-matroska",
            ".webm": "video/webm",
        }
        return mapping.get(extension.lower(), "video/mp4")
