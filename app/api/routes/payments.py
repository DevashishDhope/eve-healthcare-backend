import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, verify_webhook_secret
from app.models.user import User
from app.models.payment import Payment
from app.schemas.payment import (
    SimulatedPaymentRequest,
    PaymentResponse,
    PaymentWebhookPayload,
    WebhookResponse,
)
from app.services.payment_service import PaymentService
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_200_OK)
def simulate_payment(
    payload: SimulatedPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulate a payment for a booking.
    Accepts simulate_outcome='SUCCESS' or 'FAILED'.
    Atomically updates booking status to CONFIRMED or FAILED.
    """
    return PaymentService.process_simulated_payment(db, current_user.id, payload)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve details of a specific payment transaction."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    # Check ownership via booking
    if payment.booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this payment"
        )
    return payment


@router.post("/webhook", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
def payment_webhook(
    payload: PaymentWebhookPayload,
    _authorized: bool = Depends(verify_webhook_secret),
    db: Session = Depends(get_db)
):
    """
    Idempotent payment webhook receiver.
    Accepts external provider payment-status updates.
    Enforces UNIQUE(event_id) and database-level idempotency.
    """
    return WebhookService.process_payment_webhook(db, payload)
