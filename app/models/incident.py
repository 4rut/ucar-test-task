from enum import Enum
from sqlalchemy import Integer, Text, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class IncidentSource(str, Enum):
    OPERATOR = "OPERATOR"
    MONITORING = "MONITORING"
    PARTNER = "PARTNER"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus, name="incident_status"), nullable=False, default=IncidentStatus.OPEN
    )
    source: Mapped[IncidentSource] = mapped_column(
        SAEnum(IncidentSource, name="incident_source"), nullable=False
    )
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
