"""
Auth Controller - Endpoints de autenticacao
"""
from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
import bcrypt
import secrets
import logging
import os
import smtplib
import urllib.parse
import httpx
from datetime import datetime, timedelta
from fastapi.responses import RedirectResponse

from core.database.config import get_db, SessionLocal
from core.database.models.user import UserDB

router = APIRouter()


# ===== Modelos =====
class RegisterRequest(BaseModel):
    """Modelo de requisicao de cadastro"""
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Modelo de requisicao de login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Modelo de resposta de usuario"""
    id: str
    name: str
    email: str
    created_at: datetime


class ResetRequest(BaseModel):
    """Requisicao de recuperacao de senha"""
    email: EmailStr


class ResetConfirm(BaseModel):
    """Confirmacao de redefinicao de senha"""
    token: str
    password: str


class EmailChangeRequest(BaseModel):
    """Requisicao de alteracao de email"""
    email: EmailStr
    new_email: EmailStr


class ConfirmEmailChange(BaseModel):
    """Confirmacao de alteracao de email"""
    token: str
    new_email: EmailStr


# ===== Sessoes em memoria =====
_sessions = {}


def hash_password(password: str) -> str:
    """Gera hash seguro da senha usando bcrypt com salt automatico."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica se a senha confere com o hash armazenado."""
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


def _token_from_request(token: Optional[str] = None,
                        authorization: Optional[str] = None) -> Optional[str]:
    """Extrai o token da query string ou do header Authorization: Bearer."""
    if token:
        return token
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


def db_session_user(user_id: str):
    """Busca um usuario pelo id usando uma sessao transacional."""
    db = SessionLocal()
    try:
        return db.query(UserDB).filter(UserDB.id == user_id).first()
    finally:
        db.close()


def _envia_email(destino: str, assunto: str, corpo: str):
    """Envia email (SMTP quando configurado; senao apenas loga no modo DEV)."""
    logger = logging.getLogger("backend.auth")
    smtp_host = os.getenv("SMTP_HOST", "")
    if not smtp_host:
        logger.info("[DEV] Email para %s | %s | %s" % (destino, assunto, corpo))
        return
    try:
        from email.mime.text import MIMEText
        remetente = os.getenv("SMTP_FROM", "noreply@publisher.com")
        msg = MIMEText(corpo, "html")
        msg["Subject"] = assunto
        msg["From"] = remetente
        msg["To"] = destino
        with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", 587))) as server:
            server.starttls()
            if os.getenv("SMTP_USER"):
                server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
            server.send_message(msg)
    except Exception as e:
        logger.error("Falha ao enviar email para %s: %s" % (destino, e))


# ===== Cadastro / Login =====
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db=Depends(get_db)):
    """Cadastra um novo usuario com o email fornecido."""
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha deve ter no minimo 8 caracteres"
        )

    existing = db.query(UserDB).filter(UserDB.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ja cadastrado"
        )

    user = UserDB(
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email,
        "profile_photo": user.profile_photo,
        "created_at": (user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()),
    }

    return {
        "success": True,
        "token": token,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "profile_photo": user.profile_photo,
        }
    }


@router.post("/login")
async def login(request: LoginRequest, db=Depends(get_db)):
    """Realiza login."""
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha invalidos"
        )
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email,
        "profile_photo": user.profile_photo,
        "created_at": (user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()),
    }
    return {
        "success": True,
        "token": token,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "profile_photo": user.profile_photo,
        }
    }


@router.post("/logout")
async def logout(token: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Realiza logout."""
    tok = _token_from_request(token, authorization)
    if tok and tok in _sessions:
        del _sessions[tok]
    return {"success": True, "message": "Logout realizado com sucesso"}


# ===== Sessao / usuario autenticado =====
@router.get("/session")
async def check_session(token: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Verifica se a sessao e valida (query string ou Authorization: Bearer)."""
    tok = _token_from_request(token, authorization)
    if tok and tok in _sessions:
        session = _sessions[tok]
        user = db_session_user(session["user_id"])
        return {
            "authenticated": True,
            "user": {
                "id": session["user_id"],
                "name": session["name"],
                "email": session["email"],
                "profile_photo": session.get("profile_photo") or (user.profile_photo if user else None),
            }
        }
    return {"authenticated": False}


@router.get("/me")
async def get_me(token: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Retorna os dados do usuario autenticado."""
    tok = _token_from_request(token, authorization)
    if tok and tok in _sessions:
        session = _sessions[tok]
        user = db_session_user(session["user_id"])
        return {
            "authenticated": True,
            "user": {
                "id": session["user_id"],
                "name": session["name"],
                "email": session["email"],
                "profile_photo": session.get("profile_photo") or (user.profile_photo if user else None),
            }
        }
    return {"authenticated": False}


# ===== Recuperacao de senha =====
@router.post("/recuperar-senha")
async def request_password_reset(request: ResetRequest, db=Depends(get_db)):
    """Solicita um link de redefinicao de senha (email enviado ao usuario)."""
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        base_url = os.getenv("EMAIL_RESET_URL", "http://localhost:8000/app/redefinir-senha.html")
        link = base_url + "?token=" + token
        _envia_email(
            user.email,
            "Recuperacao de senha",
            "Clique no link para redefinir sua senha: <a href='" + link + "'>" + link + "</a>"
        )
        return {
            "success": True,
            "message": "Email de recuperacao enviado",
            "reset_link": None if os.getenv("SMTP_HOST") else link,
        }
    return {"success": True, "message": "Se o email existir, um link sera enviado"}


@router.post("/redefinir-senha")
async def reset_password(request: ResetConfirm, db=Depends(get_db)):
    """Redefine a senha usando o token recebido por email."""
    user = db.query(UserDB).filter(UserDB.reset_token == request.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Token invalido ou expirado")
    if user.reset_expires_at and user.reset_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expirado")
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Senha deve ter no minimo 8 caracteres")
    user.password_hash = hash_password(request.password)
    user.reset_token = None
    user.reset_expires_at = None
    db.commit()
    return {"success": True, "message": "Senha redefinida com sucesso"}


@router.post("/request-email-change")
async def request_email_change(request: EmailChangeRequest, db=Depends(get_db)):
    """Envia um link para confirmar a alteracao de email."""
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if not user:
        return {"success": True, "message": "Se o email existir, um link sera enviado"}
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_expires_at = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    base_url = os.getenv("EMAIL_RESET_URL", "http://localhost:8000/app/redefinir-email.html")
    link = base_url + "?token=" + token + "&email=" + urllib.parse.quote(request.new_email)
    _envia_email(
        user.email,
        "Alteracao de email",
        "Clique no link para alterar seu email: <a href='" + link + "'>" + link + "</a>"
    )
    return {
        "success": True,
        "message": "Link de alteracao enviado",
        "reset_link": None if os.getenv("SMTP_HOST") else link,
    }


@router.post("/confirm-email-change")
async def confirm_email_change(request: ConfirmEmailChange, db=Depends(get_db)):
    """Confirma a alteracao de email com o token recebido."""
    user = db.query(UserDB).filter(UserDB.reset_token == request.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Token invalido ou expirado")
    if user.reset_expires_at and user.reset_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expirado")
    user.email = request.new_email
    user.reset_token = None
    user.reset_expires_at = None
    db.commit()
    return {"success": True, "message": "Email atualizado com sucesso", "email": user.email}


# ===== Foto de perfil =====
class UpdatePhotoRequest(BaseModel):
    """Requisicao de atualizacao de foto de perfil (data URL base64)."""
    photo: str


@router.post("/update-photo")
async def update_photo(
    request: UpdatePhotoRequest,
    authorization: Optional[str] = Header(None),
    db=Depends(get_db),
):
    """Persiste a foto de perfil do usuario autenticado.

    Recebe JSON body: {"photo": "<data URL base64>"}.
    O token de autenticacao deve ser enviado no header Authorization: Bearer <token>.
    """
    tok = _token_from_request(None, authorization)
    if not (tok and tok in _sessions):
        raise HTTPException(status_code=401, detail="Nao autenticado")
    user = db.query(UserDB).filter(UserDB.id == _sessions[tok]["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    user.profile_photo = request.photo
    _sessions[tok]["profile_photo"] = request.photo
    db.commit()
    return {"success": True, "profile_photo": user.profile_photo}


# ===== Google OAuth =====
@router.get("/google")
async def google_login():
    """Redireciona o usuario para o consent screen do Google."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise HTTPException(status_code=500, detail="Google OAuth nao configurado")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "email profile",
        "access_type": "online",
    })
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + params
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(code: Optional[str] = None):
    """Troca o codigo pelo token e obtem dados do usuario."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    frontend = os.getenv("FRONTEND_URL", "http://localhost:8000/app/login.html")

    if not code:
        return RedirectResponse(frontend + "?oauth_error=missing_code")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(token_url, data=data, timeout=15)
            token_json = resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Falha ao obter token do Google")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": "Bearer " + access_token},
                timeout=15,
            )
            google_user = resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail="Erro ao consultar Google: " + str(e))

    name = google_user.get("name", "")
    email = google_user.get("email", "")
    photo = google_user.get("picture")

    db = SessionLocal()
    is_new_user = False
    try:
        user = db.query(UserDB).filter(UserDB.email == email).first()
        if not user:
            is_new_user = True
            user = UserDB(
                name=name,
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(24)),
                profile_photo=photo,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Atualizar nome e foto a cada login com Google (podem ter mudado)
            changed = False
            if name and user.name != name:
                user.name = name
                changed = True
            if photo and user.profile_photo != photo:
                user.profile_photo = photo
                changed = True
            if changed:
                db.commit()
                db.refresh(user)
    finally:
        db.close()

    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email,
        "profile_photo": user.profile_photo,
        "created_at": user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat(),
    }
    params = urllib.parse.urlencode({
        "token": token,
        "id":    str(user.id),
        "name":  user.name,
        "email": user.email,
        "photo": user.profile_photo or "",
    })

    # Conta nova: redirecionar para onboarding (configurar conexoes de redes sociais)
    # Conta existente: redirecionar direto para o dashboard
    if is_new_user:
        onboarding_url = os.getenv("FRONTEND_URL", "http://localhost:8000/app/login.html").replace(
            "login.html", "onboarding.html"
        )
        return RedirectResponse(onboarding_url + "?" + params)

    return RedirectResponse(frontend + "?" + params)
