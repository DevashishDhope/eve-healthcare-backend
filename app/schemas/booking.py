import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.schemas.catalogue import CentreTestResponse


class BookingCreate(BaseModel):
    centre_test_id: uuid.UUID
    appointment_datetime: datetime = Field(..., description="Desired appointment date and time (must be in the future)")

    @field_validator("appointment_datetime")
    @classmethod
    def validate_future_datetime(cls, v: datetime) -> datetime:
        # Normalize to UTC or check against current time
        now = datetime.now(timezone.utc)
        target = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if target <= now:
            raise ValueError("appointment_datetime must be in the future")
        return v


class BookingResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    centre_test_id: uuid.UUID
    appointment_datetime: datetime
    amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    centre_test: Optional[CentreTestResponse] = None

    model_config = ConfigDict(from_attributes=True)
