"""
Modelo de Agendamento
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Schedule(BaseModel):
    """Representa um agendamento de publicação"""
    id: Optional[str] = None
    scheduled_at: datetime = Field(..., description="Data e hora da publicação")
    status: str = Field(default="pending", description="Status: pending, completed, failed, cancelled")
    created_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "scheduled_at": "2024-12-25T10:00:00",
                "status": "pending"
            }
        }