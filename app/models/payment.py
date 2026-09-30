import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    transaction_reference: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    payment_method: Mapped[str] = mapped_column(
        String(50), default="MOCK_CARD", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('SUCCESS', 'FAILED')",
            name="chk_payment_status"
        ),
        CheckConstraint("amount >= 0", name="chk_payment_amount_positive"),
        Index(
            "uq_one_success_payment_per_booking",
            "booking_id",
            unique=True,
            postgresql_where=(status == "SUCCESS"),
        ),
    )

    booking = relationship("Booking", back_populates="payments")
