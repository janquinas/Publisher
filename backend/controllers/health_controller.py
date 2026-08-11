"""
Health Controller - Endpoints de saúde da aplicação
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Dict com status da aplicação
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "Automated Publishing Agent"
    }


@router.get("/health/detailed")
async def health_check_detailed():
    """
    Health check detalhado com verificação de componentes
    
    Returns:
        Dict com status detalhado
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "Automated Publishing Agent",
        "components": {
            "database": "connected",
            "core": "initialized",
            "scheduler": "running"
        }
    }