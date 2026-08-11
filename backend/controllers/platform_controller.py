"""
Platform Controller - Endpoints para gerenciamento de plataformas
e estrutura de redirect OAuth por plataforma.

Fluxo OAuth por plataforma:
  GET /api/platforms/{name}/oauth/start   → redireciona para a URL de autorizacao da rede
  GET /api/platforms/{name}/oauth/callback → recebe o code, troca por token e salva no banco
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import json
import urllib.parse
import httpx

from backend.auth import get_current_session
from backend.core_integration import get_core_integration
from core.database.config import get_db, SessionLocal

router = APIRouter()

# ---------------------------------------------------------------------------
# Configuracoes OAuth por plataforma (lidas de variaveis de ambiente)
# ---------------------------------------------------------------------------
_OAUTH_CFG: Dict[str, Dict] = {
    "instagram": {
        "auth_url":    "https://api.instagram.com/oauth/authorize",
        "token_url":   "https://api.instagram.com/oauth/access_token",
        "client_id":   lambda: os.getenv("INSTAGRAM_CLIENT_ID", ""),
        "client_secret": lambda: os.getenv("INSTAGRAM_CLIENT_SECRET", ""),
        "scope":       "user_profile,user_media",
        "redirect_env": "INSTAGRAM_REDIRECT_URI",
    },
    "facebook": {
        "auth_url":    "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url":   "https://graph.facebook.com/v18.0/oauth/access_token",
        "client_id":   lambda: os.getenv("FACEBOOK_APP_ID", ""),
        "client_secret": lambda: os.getenv("FACEBOOK_APP_SECRET", ""),
        "scope":       "pages_manage_posts,pages_read_engagement",
        "redirect_env": "FACEBOOK_REDIRECT_URI",
    },
    "youtube": {
        "auth_url":    "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url":   "https://oauth2.googleapis.com/token",
        "client_id":   lambda: os.getenv("YOUTUBE_CLIENT_ID", ""),
        "client_secret": lambda: os.getenv("YOUTUBE_CLIENT_SECRET", ""),
        "scope":       "https://www.googleapis.com/auth/youtube.upload",
        "redirect_env": "YOUTUBE_REDIRECT_URI",
        "extra_params": {"access_type": "offline", "prompt": "consent"},
    },
    "tiktok": {
        "auth_url":    "https://www.tiktok.com/v2/auth/authorize/",
        "token_url":   "https://open.tiktokapis.com/v2/oauth/token/",
        "client_id":   lambda: os.getenv("TIKTOK_CLIENT_KEY", ""),
        "client_secret": lambda: os.getenv("TIKTOK_CLIENT_SECRET", ""),
        "scope":       "user.info.basic,video.upload",
        "redirect_env": "TIKTOK_REDIRECT_URI",
    },
    "kwai": {
        # Kwai nao tem OAuth publico — usa access token manual
        "auth_url":    "",
        "token_url":   "",
        "client_id":   lambda: os.getenv("KWAI_CLIENT_ID", ""),
        "client_secret": lambda: os.getenv("KWAI_CLIENT_SECRET", ""),
        "scope":       "",
        "redirect_env": "KWAI_REDIRECT_URI",
    },
}

_FRONTEND_BASE = lambda: os.getenv("FRONTEND_URL", "http://localhost:8000/app/").rstrip("/index.html")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class PlatformResponse(BaseModel):
    id: str
    name: str
    enabled: bool
    connected: bool


class PlatformListResponse(BaseModel):
    platforms: List[PlatformResponse]
    total: int


class ConnectRequest(BaseModel):
    credentials: Optional[Dict[str, str]] = None


# ---------------------------------------------------------------------------
# CRUD basico
# ---------------------------------------------------------------------------
@router.get("/", response_model=PlatformListResponse)
async def list_platforms(db=Depends(get_db), session: Dict = Depends(get_current_session)):
    try:
        core = get_core_integration(db)
        db_integration = core.get_database_integration()
        platforms = db_integration.platform_repo.get_all()
        platform_list = [
            {
                "id": str(p.id),
                "name": p.name,
                "enabled": p.enabled,
                "connected": p.credentials is not None and p.credentials != "",
            }
            for p in platforms
        ]
        return {"platforms": platform_list, "total": len(platform_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar plataformas: {str(e)}")


async def _enrich_meta_credentials(credentials: dict, platform_name: str):
    """
    Após o token exchange do Facebook/Instagram, busca automaticamente
    o page_id e o ig_user_id (Instagram Professional Account ID)
    associados ao token e os adiciona ao dict de credenciais.

    Função async — usa httpx.AsyncClient para não bloquear o event loop.

    - Facebook: usa /me/accounts para obter a Page e seu page_access_token.
    - Instagram: usa /{page_id}?fields=instagram_business_account para ig_user_id.
    """
    token   = credentials.get("access_token", "")
    api_ver = "v21.0"
    base    = f"https://graph.facebook.com/{api_ver}"

    async with httpx.AsyncClient(timeout=10) as client:
        pages_resp = await client.get(
            f"{base}/me/accounts",
            params={"access_token": token, "fields": "id,name,access_token"},
        )

    if pages_resp.status_code != 200:
        return

    pages = pages_resp.json().get("data", [])
    if not pages:
        return

    page       = pages[0]
    page_id    = page["id"]
    page_token = page.get("access_token", token)

    credentials["page_id"]           = page_id
    credentials["page_name"]         = page.get("name", "")
    credentials["page_access_token"] = page_token

    # Para Instagram: buscar ig_user_id via page_access_token
    if platform_name == "instagram":
        async with httpx.AsyncClient(timeout=10) as client:
            ig_resp = await client.get(
                f"{base}/{page_id}",
                params={
                    "fields":       "instagram_business_account",
                    "access_token": page_token,
                },
            )
        if ig_resp.status_code == 200:
            ig_account = ig_resp.json().get("instagram_business_account", {})
            ig_user_id = ig_account.get("id")
            if ig_user_id:
                credentials["ig_user_id"]   = ig_user_id
                credentials["access_token"] = page_token



@router.get("/{platform_name}/status")
async def get_platform_status(platform_name: str, db=Depends(get_db), session: Dict = Depends(get_current_session)):
    try:
        core = get_core_integration(db)
        db_integration = core.get_database_integration()
        platform = db_integration.platform_repo.get_by_name(platform_name)
        if not platform:
            raise HTTPException(status_code=404, detail=f"Plataforma {platform_name} nao encontrada")
        connected = platform.credentials is not None and platform.credentials != ""
        return {
            "name": platform.name,
            "enabled": platform.enabled,
            "connected": connected,
            "status": "connected" if connected else "disconnected",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")


@router.post("/{platform_name}/connect")
async def connect_platform(platform_name: str, request: ConnectRequest, db=Depends(get_db), session: Dict = Depends(get_current_session)):
    """Conecta plataforma com credenciais manuais (access token direto)."""
    try:
        core = get_core_integration(db)
        db_integration = core.get_database_integration()
        platform = db_integration.platform_repo.get_by_name(platform_name)
        if not platform:
            raise HTTPException(status_code=404, detail=f"Plataforma {platform_name} nao encontrada")
        credentials = request.credentials or {}
        db_integration.platform_repo.update(
            str(platform.id),
            credentials=json.dumps(credentials),
            enabled=True,
        )
        return {"success": True, "message": f"{platform_name} conectada com sucesso", "platform": platform_name, "connected": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar plataforma: {str(e)}")


@router.post("/{platform_name}/disconnect")
async def disconnect_platform(platform_name: str, db=Depends(get_db), session: Dict = Depends(get_current_session)):
    try:
        core = get_core_integration(db)
        db_integration = core.get_database_integration()
        platform = db_integration.platform_repo.get_by_name(platform_name)
        if not platform:
            raise HTTPException(status_code=404, detail=f"Plataforma {platform_name} nao encontrada")
        db_integration.platform_repo.update(str(platform.id), credentials=None, enabled=False)
        return {"success": True, "message": f"{platform_name} desconectada", "platform": platform_name, "connected": False}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao desconectar plataforma: {str(e)}")


# ---------------------------------------------------------------------------
# OAuth por plataforma
# ---------------------------------------------------------------------------
@router.get("/{platform_name}/oauth/start")
async def oauth_start(platform_name: str, token: Optional[str] = None, authorization: Optional[str] = None):
    """
    Inicia o fluxo OAuth para a plataforma.
    Redireciona o navegador para a URL de autorizacao da rede social.

    Requer autenticacao via query ?token=... ou header Authorization: Bearer.
    """
    from backend.controllers.auth_controller import _token_from_request
    from core.database.repositories.session_repository import SessionRepository
    from core.database.config import SessionLocal as _SL

    frontend_base = _FRONTEND_BASE()
    conexoes_url  = frontend_base + "/conexoes.html"

    tok = _token_from_request(token, authorization)
    _db = _SL()
    try:
        _sess_valid = bool(tok and SessionRepository(_db).get_by_token(tok))
    finally:
        _db.close()

    if not _sess_valid:
        # Sessão inválida ou expirada → redirecionar para login
        return RedirectResponse(frontend_base + "/login.html?next=" + urllib.parse.quote(conexoes_url))

    cfg = _OAUTH_CFG.get(platform_name.lower())
    if not cfg or not cfg["auth_url"]:
        return RedirectResponse(
            conexoes_url + "?oauth_error=" + urllib.parse.quote(
                f"OAuth não disponível para {platform_name}"
            )
        )

    client_id = cfg["client_id"]()
    if not client_id:
        # Credenciais não configuradas no .env → redirecionar com erro claro
        env_var = platform_name.upper() + "_CLIENT_ID"
        if platform_name.lower() == "tiktok":
            env_var = "TIKTOK_CLIENT_KEY"
        elif platform_name.lower() == "facebook":
            env_var = "FACEBOOK_APP_ID"
        return RedirectResponse(
            conexoes_url + "?oauth_error=" + urllib.parse.quote(
                f"Credenciais OAuth de {platform_name} não configuradas no servidor. "
                f"Defina {env_var} no arquivo .env e reinicie o servidor."
            )
        )

    redirect_uri = os.getenv(
        cfg["redirect_env"],
        f"http://localhost:8000/api/platforms/{platform_name}/oauth/callback"
    )

    # state codifica o token do usuario para recuperar a sessao no callback
    state = urllib.parse.quote(tok)

    params = {
        "client_id":     client_id,
        "redirect_uri":  redirect_uri,
        "scope":         cfg["scope"],
        "response_type": "code",
        "state":         state,
    }
    params.update(cfg.get("extra_params", {}))

    auth_url = cfg["auth_url"] + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(auth_url)


@router.get("/{platform_name}/oauth/callback")
async def oauth_callback(
    platform_name: str,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """
    Recebe o callback OAuth da plataforma, troca o code por access_token
    e salva as credenciais no banco de dados.
    """
    from core.database.repositories.session_repository import SessionRepository
    from core.database.config import SessionLocal as _SL

    frontend_base = _FRONTEND_BASE()
    conexoes_url = frontend_base + "/conexoes.html"

    if error:
        return RedirectResponse(conexoes_url + "?oauth_error=" + urllib.parse.quote(error))

    if not code:
        return RedirectResponse(conexoes_url + "?oauth_error=missing_code")

    # Recuperar sessao pelo state
    user_token = urllib.parse.unquote(state or "")
    if user_token:
        _db = _SL()
        try:
            _tok_valid = bool(SessionRepository(_db).get_by_token(user_token))
        finally:
            _db.close()
    else:
        _tok_valid = False

    if not _tok_valid:
        return RedirectResponse(conexoes_url + "?oauth_error=invalid_state")

    cfg = _OAUTH_CFG.get(platform_name.lower())
    if not cfg or not cfg["token_url"]:
        return RedirectResponse(conexoes_url + f"?oauth_error=unsupported_{platform_name}")

    client_id = cfg["client_id"]()
    client_secret = cfg["client_secret"]()
    redirect_uri = os.getenv(
        cfg["redirect_env"],
        f"http://localhost:8000/api/platforms/{platform_name}/oauth/callback"
    )

    # Trocar code por access_token
    try:
        # TikTok v2 usa application/x-www-form-urlencoded e client_key (não client_id)
        is_tiktok = platform_name.lower() == "tiktok"
        post_data = {
            "redirect_uri":    redirect_uri,
            "grant_type":      "authorization_code",
            "code":            code,
        }
        if is_tiktok:
            post_data["client_key"]    = client_id
            post_data["client_secret"] = client_secret
        else:
            post_data["client_id"]     = client_id
            post_data["client_secret"] = client_secret

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                cfg["token_url"],
                data=post_data,
                headers={"Content-Type": "application/x-www-form-urlencoded",
                         "Cache-Control": "no-cache"},
                timeout=15,
            )
            token_data = resp.json()
    except Exception as e:
        return RedirectResponse(conexoes_url + "?oauth_error=" + urllib.parse.quote(str(e)))

    if "error" in token_data or "access_token" not in token_data:
        err_msg = (token_data.get("error_description")
                   or token_data.get("error_message")
                   or token_data.get("error", "token_exchange_failed"))
        return RedirectResponse(conexoes_url + "?oauth_error=" + urllib.parse.quote(str(err_msg)))

    access_token = token_data.get("access_token", "")
    credentials = {
        "access_token":  access_token,
        "token_type":    token_data.get("token_type", "bearer"),
    }
    # Salvar open_id do TikTok (necessário para algumas chamadas futuras)
    if "open_id" in token_data:
        credentials["open_id"] = token_data["open_id"]
    # Salvar refresh_token quando presente (TikTok, YouTube, Facebook)
    if "refresh_token" in token_data:
        credentials["refresh_token"] = token_data["refresh_token"]
    if "refresh_expires_in" in token_data:
        credentials["refresh_expires_in"] = token_data["refresh_expires_in"]
    if "expires_in" in token_data:
        credentials["expires_in"] = token_data["expires_in"]

    # Para Facebook e Instagram, buscar page_id e ig_user_id após o token exchange
    if platform_name in ("facebook", "instagram"):
        try:
            await _enrich_meta_credentials(credentials, platform_name)
        except Exception as e:
            # Não bloquear o fluxo — as credenciais parciais já são úteis
            import logging
            logging.getLogger("platform_controller").warning(
                f"Não foi possível enriquecer credenciais de {platform_name}: {e}"
            )

    # Salvar no banco
    db = SessionLocal()
    try:
        from backend.core_integration import get_core_integration as _gci
        core = _gci(db)
        db_integration = core.get_database_integration()
        platform = db_integration.platform_repo.get_by_name(platform_name)
        if platform:
            db_integration.platform_repo.update(
                str(platform.id),
                credentials=json.dumps(credentials),
                enabled=True,
            )
    finally:
        db.close()

    return RedirectResponse(conexoes_url + f"?oauth_success={platform_name}")
