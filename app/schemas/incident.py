from pydantic import BaseModel, Field
from datetime import datetime
from app.models.incident import IncidentStatus, IncidentSource


class IncidentCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=10_000)
    source: IncidentSource
    status: IncidentStatus | None = None


class IncidentOut(BaseModel):
    id: int
    description: str
    status: IncidentStatus
    source: IncidentSource
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentUpdateStatus(BaseModel):
    status: IncidentStatus
