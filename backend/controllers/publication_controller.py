"""
Publication Controller - Endpoints para gerenciamento de publicações
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from backend.auth import get_current_session
from backend.core_integration import get_core_integration
from backend.validators.publication_validator import PublicationValidator
from backend.mappers.request_mapper import RequestMapper
from backend.mappers.response_mapper import ResponseMapper
from core.database.config import get_db

router = APIRouter()


# ===== Modelos =====
class PublicationRequest(BaseModel):
    """Modelo de requisição de criação de publicação"""
    title: str
    description: Optional[str] = ""
    platforms: List[str]
    scheduled_at: Optional[datetime] = None
    media_path: Optional[str] = None
    media_size_mb: Optional[float] = None
    media_format: Optional[str] = None


class PublicationResponse(BaseModel):
    """Modelo de resposta de publicação"""
    id: str
    title: str
    description: str
    platforms: List[str]
    status: str
    scheduled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class PublicationListResponse(BaseModel):
    """Modelo de resposta de lista de publicações"""
    publications: List[PublicationResponse]
    total: int


# ===== Endpoints =====
@router.post("/", response_model=PublicationResponse, status_code=status.HTTP_201_CREATED)
async def create_publication(
    publication: PublicationRequest,
    db=Depends(get_db),
    session: Dict = Depends(get_current_session),
):
    """Cria uma nova publicação."""
    try:
        validated = PublicationValidator.validate_publication_data(
            title=publication.title,
            description=publication.description,
            platforms=publication.platforms,
            scheduled_at=publication.scheduled_at,
        )

        core = get_core_integration(db)
        publication_service = core.get_publication_service()

        result = publication_service.create_publication(
            title=validated["title"],
            description=validated["description"],
            platforms=validated["platforms"],
            media_path=publication.media_path,
            media_size_mb=publication.media_size_mb or 0.0,
            media_format=publication.media_format or "mp4",
            scheduled_at=validated["scheduled_at"],
        )

        return ResponseMapper.to_publication_response(result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar publicação: {str(e)}")


@router.get("/", response_model=PublicationListResponse)
async def list_publications(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db),
    session: Dict = Depends(get_current_session),
):
    """Lista todas as publicações com suporte a paginação via skip/limit."""
    try:
        core = get_core_integration(db)
        publication_service = core.get_publication_service()
        publications = publication_service.list_publications()
        total = len(publications)
        paginated = publications[skip: skip + limit] if limit > 0 else publications[skip:]
        return ResponseMapper.to_publication_list_response(paginated, total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar publicações: {str(e)}")


@router.get("/{publication_id}", response_model=PublicationResponse)
async def get_publication(
    publication_id: str,
    db=Depends(get_db),
    session: Dict = Depends(get_current_session),
):
    """Busca uma publicação por ID."""
    try:
        core = get_core_integration(db)
        publication_service = core.get_publication_service()
        publication = publication_service.get_publication(publication_id)

        if not publication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Publicação {publication_id} não encontrada",
            )

        return ResponseMapper.to_publication_response(publication)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar publicação: {str(e)}")


@router.put("/{publication_id}", response_model=PublicationResponse)
async def update_publication(
    publication_id: str,
    publication: PublicationRequest,
    db=Depends(get_db),
    session: Dict = Depends(get_current_session),
):
    """Atualiza uma publicação."""
    try:
        validated = PublicationValidator.validate_publication_data(
            title=publication.title,
            description=publication.description,
            platforms=publication.platforms,
            scheduled_at=publication.scheduled_at,
        )

        core = get_core_integration(db)
        publication_service = core.get_publication_service()

        result = publication_service.update_publication(
            publication_id=publication_id,
            title=validated["title"],
            description=validated["description"],
            platforms=validated["platforms"],
            scheduled_at=validated["scheduled_at"],
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Publicação {publication_id} não encontrada",
            )

        return ResponseMapper.to_publication_response(result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar publicação: {str(e)}")


@router.delete("/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_publication(
    publication_id: str,
    db=Depends(get_db),
    session: Dict = Depends(get_current_session),
):
    """Remove uma publicação."""
    try:
        core = get_core_integration(db)
        publication_service = core.get_publication_service()
        deleted = publication_service.delete_publication(publication_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Publicação {publication_id} não encontrada",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir publicação: {str(e)}")


@router.post("/{publication_id}/publish", response_model=PublicationResponse)
async def publish_now(
    publication_id: str,
    db=Depends(get_db),
    session: Dict = Depends(get_current_session),
):
    """Publica imediatamente."""
    try:
        core = get_core_integration(db)
        publication_service = core.get_publication_service()
        result = publication_service.publish_now(publication_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Publicação {publication_id} não encontrada",
            )

        return ResponseMapper.to_publication_response(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao publicar: {str(e)}")


@router.post("/{publication_id}/cancel")
async def cancel_publication(
    publication_id: str,
    db=Depends(get_db),
    session: Dict = Depends(get_current_session),
):
    """Cancela uma publicação agendada."""
    try:
        core = get_core_integration(db)
        publication_service = core.get_publication_service()
        cancelled = publication_service.cancel_publication(publication_id)

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agendamento {publication_id} não encontrado",
            )

        return ResponseMapper.to_success_response(
            message=f"Publicação {publication_id} cancelada com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar publicação: {str(e)}")
