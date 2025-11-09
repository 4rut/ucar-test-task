from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from app.api.deps import get_db
from app.models.incident import Incident, IncidentStatus
from app.schemas.incident import IncidentCreate, IncidentOut, IncidentUpdateStatus

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)) -> IncidentOut:
    status_value = payload.status or IncidentStatus.OPEN
    row = Incident(description=payload.description, source=payload.source, status=status_value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=List[IncidentOut])
def list_incidents(
        status_filter: IncidentStatus | None = Query(default=None, alias="status"),
        db: Session = Depends(get_db)
) -> list[IncidentOut]:
    stmt = select(Incident).order_by(Incident.id)
    if status_filter:
        stmt = stmt.where(Incident.status == status_filter)
    rows = db.execute(stmt).scalars().all()
    return rows


@router.patch("/{incident_id}/status", response_model=IncidentOut)
def update_status(
        incident_id: int, payload: IncidentUpdateStatus, db: Session = Depends(get_db)
) -> IncidentOut:
    row = db.get(Incident, incident_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    row.status = payload.status
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
