"""
TikTok Adapter - Publicação real de vídeos via TikTok Content Posting API v2

Fluxo de upload (FILE_UPLOAD):
  1. POST /v2/post/publish/inbox/video/init/
     Registra o upload e recebe { publish_id, upload_url }
  2. PUT <upload_url>  (binário do vídeo em um único chunk ou em múltiplos)
     Envia o arquivo para os servidores do TikTok
  3. O vídeo vai para a caixa de entrada do usuário como rascunho.
     O usuário recebe uma notificação no app e finaliza a postagem.

Nota importante sobre a modalidade de publicação:
  - O endpoint /inbox/video/init/ cria um RASCUNHO na caixa de entrada.
    O usuário precisa abrir o TikTok e confirmar a publicação.
  - O endpoint /v2/post/publish/video/init/ (Direct Post) publica direto,
    mas exige aprovação especial do TikTok para aplicações de terceiros.
  - Para a maioria dos desenvolvedores o fluxo de inbox é o disponível.

Autenticação:
  - credentials["access_token"]  : token OAuth 2.0 do usuário (válido 24h)
  - credentials["refresh_token"] : token de renovação (válido 365 dias)
  - credentials["open_id"]       : identificador único do usuário no app

Referências:
  https://developers.tiktok.com/doc/content-posting-api-reference-upload-video/
  https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide/
  https://developers.tiktok.com/doc/oauth-user-access-token-management/
"""
from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Dict, Optional, Any

import requests

from ..models.result import Result
from ..models.media import Media
from .base_adapter import BasePlatformAdapter

# Endpoints da TikTok Content Posting API v2
_BASE_URL        = "https://open.tiktokapis.com"
_INIT_UPLOAD_URL = f"{_BASE_URL}/v2/post/publish/inbox/video/init/"
_STATUS_URL      = f"{_BASE_URL}/v2/post/publish/status/fetch/"
_TOKEN_URL       = f"{_BASE_URL}/v2/oauth/token/"
_USER_INFO_URL   = f"{_BASE_URL}/v2/user/info/"

# Tamanho de chunk: 10 MB (deve ser >= 5 MB, exceto o último)
_CHUNK_SIZE   = 10 * 1024 * 1024   # 10 MB
_MIN_CHUNK    =  5 * 1024 * 1024   #  5 MB (mínimo exigido pela API)
_MAX_CHUNKS   = 1000


class TikTokAdapter(BasePlatformAdapter):
    """Adaptador de publicação real para o TikTok via Content Posting API v2."""

    def __init__(self):
        super().__init__("tiktok")

    # ------------------------------------------------------------------
    # Contrato da BasePlatformAdapter
    # ------------------------------------------------------------------

    def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        if not credentials.get("access_token"):
            self.log_warning("access_token ausente nas credenciais do TikTok")
            return False
        return True

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Valida o token fazendo uma chamada leve à API de informações do usuário.
        Renova automaticamente via refresh_token se receber 401.
        """
        if not self.validate_credentials(credentials):
            return False

        resp = requests.get(
            _USER_INFO_URL,
            params={"fields": "open_id"},
            headers=self._auth_headers(credentials),
            timeout=10,
        )

        if resp.status_code == 401:
            self.log_info("access_token expirado, tentando renovar...")
            new_token = self._refresh_access_token(credentials)
            if not new_token:
                self.log_error("Falha ao renovar access_token do TikTok")
                return False
            credentials["access_token"] = new_token
            resp = requests.get(
                _USER_INFO_URL,
                params={"fields": "open_id"},
                headers=self._auth_headers(credentials),
                timeout=10,
            )

        if resp.status_code == 200:
            data = resp.json()
            # A API retorna error.code == "ok" quando bem-sucedido
            if data.get("error", {}).get("code") == "ok":
                self.log_info("Autenticação com TikTok OK")
                return True

        self.log_error(
            f"Falha na autenticação com TikTok: {resp.status_code} {resp.text[:200]}"
        )
        return False

    def prepare_request(
        self,
        media: Media,
        title: str,
        description: str,
        credentials: Dict[str, str],
    ) -> Dict[str, Any]:
        """Monta o payload de inicialização do upload."""
        file_size  = Path(media.file_path).stat().st_size
        chunk_size = self._calc_chunk_size(file_size)
        total_chunks = math.ceil(file_size / chunk_size)

        return {
            "source_info": {
                "source":            "FILE_UPLOAD",
                "video_size":        file_size,
                "chunk_size":        chunk_size,
                "total_chunk_count": total_chunks,
            }
        }

    def publish(
        self,
        media: Media,
        title: str,
        description: str,
        credentials: Dict[str, str],
    ) -> Result:
        """
        Faz o upload real do vídeo para o TikTok (inbox/rascunho).

        Fluxo:
          1. Autenticar (renova token se necessário).
          2. Inicializar upload → obter upload_url e publish_id.
          3. Enviar arquivo em chunks via PUT.
          4. Retornar Result com publish_id e link de acompanhamento.
        """
        credentials = self._parse_credentials(credentials)

        try:
            self.log_info("Iniciando publicação no TikTok", title=title)

            # 1. Autenticar
            if not self.authenticate(credentials):
                return Result(
                    platform_name="tiktok",
                    success=False,
                    message="Falha na autenticação com TikTok. "
                            "Verifique se a conta está conectada em Conexões.",
                    error_code="AUTH_ERROR",
                )

            # 2. Verificar arquivo
            file_path = Path(media.file_path)
            if not file_path.exists():
                return Result(
                    platform_name="tiktok",
                    success=False,
                    message=f"Arquivo de vídeo não encontrado: {media.file_path}",
                    error_code="FILE_NOT_FOUND",
                )

            # 3. Inicializar upload
            payload    = self.prepare_request(media, title, description, credentials)
            init_resp  = requests.post(
                _INIT_UPLOAD_URL,
                headers={**self._auth_headers(credentials),
                         "Content-Type": "application/json; charset=UTF-8"},
                json=payload,
                timeout=30,
            )
            init_data  = init_resp.json()

            if init_resp.status_code != 200 or init_data.get("error", {}).get("code") != "ok":
                err = (init_data.get("error", {}).get("message")
                       or init_data.get("error", {}).get("code", "init_failed"))
                self.log_error(f"Falha ao iniciar upload no TikTok: {err}")
                return Result(
                    platform_name="tiktok",
                    success=False,
                    message=f"Falha ao iniciar upload: {err}",
                    error_code="UPLOAD_INIT_ERROR",
                )

            upload_url = init_data["data"]["upload_url"]
            publish_id = init_data["data"]["publish_id"]
            self.log_info("Upload TikTok iniciado", publish_id=publish_id)

            # 4. Enviar arquivo
            success = self._upload_file(upload_url, file_path, payload)
            if not success:
                return Result(
                    platform_name="tiktok",
                    success=False,
                    message="Falha ao enviar o vídeo para o TikTok.",
                    error_code="UPLOAD_ERROR",
                )

            # 5. Sucesso — o vídeo está na inbox do usuário aguardando confirmação
            self.log_info(
                "Vídeo enviado para TikTok com sucesso — aguardando confirmação do usuário",
                publish_id=publish_id,
            )
            return Result(
                platform_name="tiktok",
                success=True,
                message=(
                    "Vídeo enviado para o TikTok. "
                    "O usuário receberá uma notificação no app para revisar e publicar."
                ),
                post_url=f"https://www.tiktok.com/inbox",
                published_at=__import__("datetime").datetime.now(),
            )

        except requests.exceptions.ConnectionError:
            return Result(
                platform_name="tiktok",
                success=False,
                message="Sem conexão com a internet ao tentar publicar no TikTok.",
                error_code="CONNECTION_ERROR",
            )
        except requests.exceptions.Timeout:
            return Result(
                platform_name="tiktok",
                success=False,
                message="Timeout ao publicar no TikTok. Tente novamente.",
                error_code="TIMEOUT_ERROR",
            )
        except Exception as e:
            self.log_error(f"Erro inesperado na publicação no TikTok: {e}")
            return Result(
                platform_name="tiktok",
                success=False,
                message=f"Erro inesperado: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    def get_upload_url(self, credentials: Dict[str, str]) -> Optional[str]:
        return _INIT_UPLOAD_URL

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _auth_headers(self, credentials: Dict[str, str]) -> Dict[str, str]:
        return {"Authorization": f"Bearer {credentials.get('access_token', '')}"}

    def _parse_credentials(self, credentials) -> Dict[str, str]:
        """Garante que credentials é um dict (banco salva como JSON string)."""
        if isinstance(credentials, str):
            try:
                return json.loads(credentials)
            except (json.JSONDecodeError, TypeError):
                return {}
        return dict(credentials) if credentials else {}

    def _calc_chunk_size(self, file_size: int) -> int:
        """
        Calcula o tamanho ideal de cada chunk.

        Regras da API:
          - Tamanho < 5 MB  → enviar em 1 chunk igual ao tamanho total
          - Tamanho > 64 MB → obrigatório usar múltiplos chunks
          - Máximo de 1000 chunks
          - Cada chunk deve ser >= 5 MB (exceto o último)
        """
        if file_size < _MIN_CHUNK:
            return file_size
        # Garantir no máximo 1000 chunks
        min_chunk_for_limit = math.ceil(file_size / _MAX_CHUNKS)
        return max(_CHUNK_SIZE, min_chunk_for_limit)

    def _upload_file(
        self,
        upload_url: str,
        file_path: Path,
        payload: Dict[str, Any],
    ) -> bool:
        """
        Envia o arquivo de vídeo para o upload_url usando PUT com chunking.
        Retorna True em caso de sucesso, False em caso de falha.
        """
        file_size   = file_path.stat().st_size
        chunk_size  = payload["source_info"]["chunk_size"]
        mime        = self._mime_type(file_path.suffix)
        max_retries = 3
        uploaded    = 0

        with open(file_path, "rb") as f:
            while uploaded < file_size:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                chunk_end = uploaded + len(chunk) - 1
                headers   = {
                    "Content-Type":   mime,
                    "Content-Length": str(len(chunk)),
                    "Content-Range":  f"bytes {uploaded}-{chunk_end}/{file_size}",
                }

                attempt = 0
                while attempt < max_retries:
                    resp = requests.put(
                        upload_url,
                        headers=headers,
                        data=chunk,
                        timeout=120,
                    )

                    # TikTok retorna 2xx ao aceitar o chunk
                    if resp.status_code in (200, 201, 204):
                        uploaded += len(chunk)
                        self.log_info(
                            f"Progresso TikTok: {uploaded}/{file_size} bytes "
                            f"({100 * uploaded // file_size}%)"
                        )
                        break

                    # Erro recuperável (5xx) — retry com backoff
                    if resp.status_code >= 500:
                        attempt += 1
                        wait = 2 ** attempt
                        self.log_warning(
                            f"Erro {resp.status_code} no upload TikTok, "
                            f"tentativa {attempt}/{max_retries}. Aguardando {wait}s..."
                        )
                        time.sleep(wait)
                        continue

                    # Erro não recuperável (4xx)
                    self.log_error(
                        f"Erro fatal no upload TikTok: {resp.status_code} {resp.text[:200]}"
                    )
                    return False
                else:
                    self.log_error("Upload TikTok falhou após máximo de tentativas")
                    return False

        self.log_info("Upload TikTok concluído com sucesso")
        return True

    def _refresh_access_token(self, credentials: Dict[str, str]) -> Optional[str]:
        """
        Renova o access_token usando o refresh_token via TikTok OAuth v2.
        Persiste o novo token no banco automaticamente.
        """
        refresh_token = credentials.get("refresh_token", "")
        if not refresh_token:
            self.log_warning("refresh_token ausente — não é possível renovar o token TikTok")
            return None

        client_key    = os.getenv("TIKTOK_CLIENT_KEY", "")
        client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "")

        if not client_key or not client_secret:
            self.log_error(
                "TIKTOK_CLIENT_KEY ou TIKTOK_CLIENT_SECRET não configurados no .env"
            )
            return None

        try:
            resp = requests.post(
                _TOKEN_URL,
                data={
                    "client_key":    client_key,
                    "client_secret": client_secret,
                    "grant_type":    "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cache-Control": "no-cache",
                },
                timeout=15,
            )
            data = resp.json()
            new_token = data.get("access_token")

            if new_token:
                self.log_info("access_token TikTok renovado com sucesso")
                # Atualizar credenciais em memória e persistir no banco
                credentials["access_token"] = new_token
                if "refresh_token" in data:
                    credentials["refresh_token"] = data["refresh_token"]
                if "refresh_expires_in" in data:
                    credentials["refresh_expires_in"] = data["refresh_expires_in"]
                self._persist_new_token(credentials)
            else:
                self.log_error(f"Resposta inesperada ao renovar token TikTok: {data}")

            return new_token
        except Exception as e:
            self.log_error(f"Erro ao renovar access_token TikTok: {e}")
            return None

    def _persist_new_token(self, credentials: Dict[str, str]):
        """Persiste as credenciais atualizadas no banco (best-effort)."""
        try:
            from core.database.config import SessionLocal
            from core.database.repositories.platform_repository import PlatformRepository

            db = SessionLocal()
            try:
                repo     = PlatformRepository(db)
                platform = repo.get_by_name("tiktok")
                if platform:
                    repo.update(str(platform.id), credentials=json.dumps(credentials))
            finally:
                db.close()
        except Exception as e:
            self.log_warning(f"Não foi possível persistir o token TikTok renovado: {e}")

    @staticmethod
    def _mime_type(extension: str) -> str:
        mapping = {
            ".mp4":  "video/mp4",
            ".mov":  "video/quicktime",
            ".webm": "video/webm",
        }
        return mapping.get(extension.lower(), "video/mp4")
