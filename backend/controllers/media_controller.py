"""
Media Controller - Endpoints para gerenciamento de videos/midia
"""
import os
import uuid
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import FileResponse

from backend.auth import get_current_session
from core.database.config import get_db
from core.database.repositories.publication_repository import PublicationRepository
from core.database.repositories.schedule_repository import ScheduleRepository
from core.config import ALLOWED_VIDEO_EXTENSIONS as _ALLOWED_EXT, MAX_VIDEO_SIZE_MB as _MAX_SIZE_MB

router = APIRouter()

UPLOAD_DIR = os.path.join("backend", "static", "uploads")
# Usa as constantes canônicas de core/config.py
ALLOWED_EXTENSIONS = {ext if ext.startswith(".") else f".{ext}" for ext in _ALLOWED_EXT}


class MediaListResponse(BaseModel):
    id: str
    title: str
    description: str
    media_path: str
    media_size_mb: str
    media_format: str
    duration_seconds: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime


class MediaListResponsePage(BaseModel):
    media: List[MediaListResponse]
    total: int


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    title: str = Form(""),
    description: str = Form(""),
    platforms: str = Form("[]"),
    scheduled_at: Optional[str] = Form(None),
    db=Depends(get_db),
    session: Dict = Depends(get_current_session),
):
    """
    Importa um video: salva no disco e cria a publicacao no banco de dados.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Formato nao suportado: {ext}. Permitidos: {sorted(ALLOWED_EXTENSIONS)}")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{file.filename}"
    dest = os.path.join(UPLOAD_DIR, stored_name)

    # Stream para disco
    size_bytes = 0
    with open(dest, "wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            size_bytes += len(chunk)
    await file.close()

    size_mb = round(size_bytes / (1024 * 1024), 2)
    media_format = ext.lstrip(".")

    pub_repo = PublicationRepository(db)
    sched_repo = ScheduleRepository(db)

    pub = pub_repo.create(
        title=title or os.path.splitext(file.filename)[0],
        description=description,
        media_path=stored_name,
        media_size_mb=str(size_mb),
        media_format=media_format,
        platforms=platforms,  # already a JSON string from Form("[]")
        is_media_only=True,   # marca como entrada de biblioteca, não publicação agendada
    )

    sched = None
    if scheduled_at:
        try:
            sched_dt = datetime.fromisoformat(scheduled_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data invalido")
        sched = sched_repo.create(publication_id=pub.id, scheduled_at=sched_dt, status="pending")

    return {
        "success": True,
        "media": {
            "id": str(pub.id),
            "title": pub.title,
            "description": pub.description,
            "media_path": pub.media_path,
            "media_size_mb": pub.media_size_mb,
            "media_format": pub.media_format,
            "duration_seconds": pub.duration_seconds,
            "scheduled_at": sched.scheduled_at.isoformat() if sched else None,
            "status": "scheduled" if sched else "pending",
            "created_at": pub.created_at.isoformat() if pub.created_at else None,
            "updated_at": pub.updated_at.isoformat() if pub.updated_at else None,
        },
    }


@router.get("/", response_model=MediaListResponsePage)
async def list_media(db=Depends(get_db), session: Dict = Depends(get_current_session)):
    """Lista apenas os vídeos da biblioteca de mídia (uploads diretos)."""
    pub_repo = PublicationRepository(db)
    pubs = pub_repo.get_all_media()
    items = []
    for p in pubs:
        sched = next(iter(p.schedules or []), None)
        items.append(MediaListResponse(
            id=str(p.id), title=p.title, description=p.description,
            media_path=p.media_path, media_size_mb=p.media_size_mb,
            media_format=p.media_format, duration_seconds=p.duration_seconds,
            scheduled_at=sched.scheduled_at if sched else None,
            status="scheduled" if sched else "pending",
            created_at=p.created_at, updated_at=p.updated_at,
        ))
    return {"media": items, "total": len(items)}


@router.get("/{media_id}", response_model=MediaListResponse)
async def get_media(media_id: str, db=Depends(get_db), session: Dict = Depends(get_current_session)):
    """Obtem um video/publicacao por id."""
    pub_repo = PublicationRepository(db)
    p = pub_repo.get_by_id(media_id)
    if not p:
        raise HTTPException(status_code=404, detail="Video nao encontrado")
    return MediaListResponse(
        id=str(p.id), title=p.title, description=p.description,
        media_path=p.media_path, media_size_mb=p.media_size_mb,
        media_format=p.media_format, duration_seconds=p.duration_seconds,
        scheduled_at=(p.schedules[0].scheduled_at if p.schedules else None),
        status="scheduled" if p.schedules else "pending",
        created_at=p.created_at, updated_at=p.updated_at,
    )


@router.put("/{media_id}")
async def update_media(media_id: str, title: str = Form(""), description: str = Form(""),
                       scheduled_at: Optional[str] = Form(None), db=Depends(get_db),
                       session: Dict = Depends(get_current_session)):
    """Edita titulo, descricao e agendamento de um video."""
    pub_repo = PublicationRepository(db)
    sched_repo = ScheduleRepository(db)
    p = pub_repo.get_by_id(media_id)
    if not p:
        raise HTTPException(status_code=404, detail="Video nao encontrado")
    p.title = title
    p.description = description
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    # redefinir agendamento quando informado
    if scheduled_at:
        try:
            sched_dt = datetime.fromisoformat(scheduled_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data invalido")
        # remove agendamentos existentes e cria um novo
        for s in list(p.schedules or []):
            db.delete(s)
        sched_repo.create(publication_id=p.id, scheduled_at=sched_dt, status="pending")
    return {"success": True, "message": "Video atualizado com sucesso"}


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(media_id: str, db=Depends(get_db), session: Dict = Depends(get_current_session)):
    """Remove um video/publicacao (e o arquivo do disco)."""
    pub_repo = PublicationRepository(db)
    p = pub_repo.get_by_id(media_id)
    if not p:
        raise HTTPException(status_code=404, detail="Video nao encontrado")
    # remover arquivo do disco
    file_path = os.path.join(UPLOAD_DIR, p.media_path)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass
    pub_repo.delete(p.id)
    return None


@router.get("/{media_id}/download")
async def download_media(media_id: str, db=Depends(get_db), session: Dict = Depends(get_current_session)):
    """Retorna o arquivo de video para preview/download."""
    pub_repo = PublicationRepository(db)
    p = pub_repo.get_by_id(media_id)
    if not p:
        raise HTTPException(status_code=404, detail="Video nao encontrado")
    file_path = os.path.join(UPLOAD_DIR, p.media_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")
    return FileResponse(file_path, media_type="video/mp4")