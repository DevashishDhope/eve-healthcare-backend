import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PROCESSED"
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    booking = relationship("Booking", back_populates="webhook_events")
