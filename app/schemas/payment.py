import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class SimulatedPaymentRequest(BaseModel):
    booking_id: uuid.UUID
    simulate_outcome: str = Field(default="SUCCESS", description="Simulated result: SUCCESS or FAILED")
    payment_method: str = Field(default="MOCK_CARD", description="Payment method used")

    @field_validator("simulate_outcome")
    @classmethod
    def validate_outcome(cls, v: str) -> str:
        upper_v = v.strip().upper()
        if upper_v not in ("SUCCESS", "FAILED"):
            raise ValueError("simulate_outcome must be either 'SUCCESS' or 'FAILED'")
        return upper_v


class PaymentResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    transaction_reference: str
    amount: Decimal
    status: str
    payment_method: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookDataPayload(BaseModel):
    booking_id: uuid.UUID
    payment_reference: str = Field(..., min_length=1)
    status: str
    amount: Decimal

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        upper_v = v.strip().upper()
        if upper_v not in ("SUCCESS", "FAILED"):
            raise ValueError("Webhook data.status must be 'SUCCESS' or 'FAILED'")
        return upper_v


class PaymentWebhookPayload(BaseModel):
    event_id: str = Field(..., min_length=1, description="Unique event identifier for idempotency")
    event_type: str = Field(default="payment.updated", min_length=1)
    data: WebhookDataPayload
    timestamp: Optional[datetime] = None


class WebhookResponse(BaseModel):
    status: str
    message: str
    event_id: str
