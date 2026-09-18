import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime
from enum import Enum
from typing import Dict, Any
from ..base import Base


class EventTypesEnum(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class OutboxEvents(Base):
    __tablename__ = "outbox_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(sa.String, nullable=False)
    status: Mapped[EventTypesEnum] = mapped_column(
        sa.Enum(EventTypesEnum, create_type=True, native_enum=True, name="event_types_enum")
    )
    payload: Mapped[Dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    attempts: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(True), server_default=sa.func.now())
    processed_at: Mapped[datetime] = mapped_column(sa.DateTime(True), nullable=True)
    last_error: Mapped[datetime] = mapped_column(sa.DateTime(True), nullable=True)
