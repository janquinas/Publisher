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
from core.database.repositories.session_repository import SessionRepository

router = APIRouter()


# ===== Modelos =====
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResetRequest(BaseModel):
    email: EmailStr


class ResetConfirm(BaseModel):
    token: str
    password: str


class EmailChangeRequest(BaseModel):
    email: EmailStr
    new_email: EmailStr


class ConfirmEmailChange(BaseModel):
    token: str
    new_email: EmailStr


class UpdatePhotoRequest(BaseModel):
    photo: str


class UpdateProfileRequest(BaseModel):
    name: str


# ===== Helpers de senha =====
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


def _token_from_request(
    token: Optional[str] = None,
    authorization: Optional[str] = None,
) -> Optional[str]:
    """Extrai o token da query string ou do header Authorization: Bearer."""
    if token:
        return token
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


# ===== Sessões — acesso ao banco =====
def _get_session_data(token: str) -> Optional[dict]:
    """
    Busca a sessão no banco pelo token.
    Retorna dict compatível com o formato antigo ou None se inválida/expirada.
    """
    db = SessionLocal()
    try:
        repo = SessionRepository(db)
        sess = repo.get_by_token(token)
        if not sess:
            return None
        return {
            "user_id":      sess.user_id,
            "name":         sess.user_name,
            "email":        sess.user_email,
            "profile_photo": sess.user_photo,
        }
    finally:
        db.close()


def _create_session(token: str, user_id: str, name: str, email: str, photo: Optional[str], db) -> None:
    """Persiste uma nova sessão no banco."""
    repo = SessionRepository(db)
    repo.create(
        token=token,
        user_id=user_id,
        user_name=name,
        user_email=email,
        user_photo=photo,
    )


def _delete_session(token: str) -> None:
    """Remove a sessão do banco."""
    db = SessionLocal()
    try:
        SessionRepository(db).delete_by_token(token)
    finally:
        db.close()


def _envia_email(destino: str, assunto: str, corpo: str):
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
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Senha deve ter no minimo 8 caracteres")

    existing = db.query(UserDB).filter(UserDB.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email ja cadastrado")

    user = UserDB(
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = secrets.token_urlsafe(32)
    _create_session(token, str(user.id), user.name, user.email, user.profile_photo, db)

    return {
        "success": True,
        "token": token,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "profile_photo": user.profile_photo,
        },
    }


@router.post("/login")
async def login(request: LoginRequest, db=Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou senha invalidos")

    token = secrets.token_urlsafe(32)
    _create_session(token, str(user.id), user.name, user.email, user.profile_photo, db)

    return {
        "success": True,
        "token": token,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "profile_photo": user.profile_photo,
        },
    }


@router.post("/logout")
async def logout(
    token: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    tok = _token_from_request(token, authorization)
    if tok:
        _delete_session(tok)
    return {"success": True, "message": "Logout realizado com sucesso"}


# ===== Sessão / usuario autenticado =====
@router.get("/session")
async def check_session(
    token: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    tok = _token_from_request(token, authorization)
    if tok:
        data = _get_session_data(tok)
        if data:
            return {"authenticated": True, "user": {"id": data["user_id"], "name": data["name"], "email": data["email"], "profile_photo": data.get("profile_photo")}}
    return {"authenticated": False}


@router.get("/me")
async def get_me(
    token: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    tok = _token_from_request(token, authorization)
    if tok:
        data = _get_session_data(tok)
        if data:
            return {"authenticated": True, "user": {"id": data["user_id"], "name": data["name"], "email": data["email"], "profile_photo": data.get("profile_photo")}}
    return {"authenticated": False}


# ===== Recuperação de senha =====
@router.post("/recuperar-senha")
async def request_password_reset(request: ResetRequest, db=Depends(get_db)):
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
            "Clique no link para redefinir sua senha: <a href='" + link + "'>" + link + "</a>",
        )
        return {
            "success": True,
            "message": "Email de recuperacao enviado",
            "reset_link": None if os.getenv("SMTP_HOST") else link,
        }
    return {"success": True, "message": "Se o email existir, um link sera enviado"}


@router.post("/redefinir-senha")
async def reset_password(request: ResetConfirm, db=Depends(get_db)):
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


# ===== Alteração de e-mail =====
@router.post("/request-email-change")
async def request_email_change(request: EmailChangeRequest, db=Depends(get_db)):
    """
    Envia link de confirmação para o novo e-mail.
    Usa email_change_token / email_change_expires_at (campos separados do reset de senha).
    """
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if not user:
        return {"success": True, "message": "Se o email existir, um link sera enviado"}
    token = secrets.token_urlsafe(32)
    user.email_change_token = token
    user.email_change_expires_at = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    base_url = os.getenv("EMAIL_RESET_URL", "http://localhost:8000/app/redefinir-email.html")
    link = base_url + "?token=" + token + "&email=" + urllib.parse.quote(request.new_email)
    _envia_email(
        user.email,
        "Alteracao de email",
        "Clique no link para alterar seu email: <a href='" + link + "'>" + link + "</a>",
    )
    return {
        "success": True,
        "message": "Link de alteracao enviado",
        "reset_link": None if os.getenv("SMTP_HOST") else link,
    }


@router.post("/confirm-email-change")
async def confirm_email_change(request: ConfirmEmailChange, db=Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email_change_token == request.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Token invalido ou expirado")
    if user.email_change_expires_at and user.email_change_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expirado")
    user.email = request.new_email
    user.email_change_token = None
    user.email_change_expires_at = None
    db.commit()
    return {"success": True, "message": "Email atualizado com sucesso", "email": user.email}


# ===== Foto de perfil =====
@router.post("/update-photo")
async def update_photo(
    request: UpdatePhotoRequest,
    authorization: Optional[str] = Header(None),
    db=Depends(get_db),
):
    tok = _token_from_request(None, authorization)
    if not tok:
        raise HTTPException(status_code=401, detail="Nao autenticado")
    session_data = _get_session_data(tok)
    if not session_data:
        raise HTTPException(status_code=401, detail="Nao autenticado")

    user = db.query(UserDB).filter(UserDB.id == session_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    user.profile_photo = request.photo
    db.commit()

    # Atualizar snapshot da foto em todas as sessões ativas do usuário
    from core.database.repositories.session_repository import SessionRepository as SR
    SR(db).update_user_photo(session_data["user_id"], request.photo)

    return {"success": True, "profile_photo": user.profile_photo}


# ===== Nome de perfil =====
@router.post("/update-profile")
async def update_profile(
    request: UpdateProfileRequest,
    authorization: Optional[str] = Header(None),
    db=Depends(get_db),
):
    """Persiste o nome do usuário no banco de dados."""
    tok = _token_from_request(None, authorization)
    if not tok:
        raise HTTPException(status_code=401, detail="Nao autenticado")
    session_data = _get_session_data(tok)
    if not session_data:
        raise HTTPException(status_code=401, detail="Nao autenticado")

    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="Nome nao pode ser vazio")

    user = db.query(UserDB).filter(UserDB.id == session_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    user.name = request.name.strip()
    db.commit()

    # Atualizar snapshot do nome em todas as sessões ativas
    from core.database.models.session import SessionDB as _SDB
    db.query(_SDB).filter(
        _SDB.user_id == session_data["user_id"]
    ).update({"user_name": user.name}, synchronize_session=False)
    db.commit()

    return {"success": True, "name": user.name}


# ===== Google OAuth =====
@router.get("/google")
async def google_login():
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
    return RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + params)


@router.get("/google/callback")
async def google_callback(code: Optional[str] = None):
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    frontend = os.getenv("FRONTEND_URL", "http://localhost:8000/app/login.html")

    if not code:
        return RedirectResponse(frontend + "?oauth_error=missing_code")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=15,
            )
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

        token = secrets.token_urlsafe(32)
        _create_session(token, str(user.id), user.name, user.email, user.profile_photo, db)
    finally:
        db.close()

    params_str = urllib.parse.urlencode({
        "token": token,
        "id":    str(user.id),
        "name":  user.name,
        "email": user.email,
        "photo": user.profile_photo or "",
    })

    if is_new_user:
        onboarding_url = frontend.replace("login.html", "onboarding.html")
        return RedirectResponse(onboarding_url + "?" + params_str)

    return RedirectResponse(frontend + "?" + params_str)
