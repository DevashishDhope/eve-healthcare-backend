from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.webhook_event import PaymentWebhookEvent
from app.schemas.payment import PaymentWebhookPayload, WebhookResponse


class WebhookService:
    @staticmethod
    def process_payment_webhook(db: Session, payload: PaymentWebhookPayload) -> WebhookResponse:
        # Step 1: Check if event_id already processed
        existing_event = (
            db.query(PaymentWebhookEvent)
            .filter(PaymentWebhookEvent.event_id == payload.event_id)
            .first()
        )
        if existing_event:
            return WebhookResponse(
                status="ignored",
                message="Duplicate event: already received and processed",
                event_id=payload.event_id,
            )

        # Step 2: Claim event_id atomically with flush to catch concurrent duplicates
        webhook_record = PaymentWebhookEvent(
            event_id=payload.event_id,
            booking_id=payload.data.booking_id,
            payment_reference=payload.data.payment_reference,
            event_type=payload.event_type,
            payload=payload.model_dump(mode="json"),
            status="PROCESSING",
        )
        db.add(webhook_record)

        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            return WebhookResponse(
                status="ignored",
                message="Duplicate event: concurrent submission detected",
                event_id=payload.event_id,
            )

        # Step 3: Retrieve booking with row lock
        booking = (
            db.query(Booking)
            .filter(Booking.id == payload.data.booking_id)
            .with_for_update()
            .first()
        )
        if not booking:
            webhook_record.status = "FAILED_BOOKING_NOT_FOUND"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking with id '{payload.data.booking_id}' not found"
            )

        # Step 4: Validate amount against historical booking price
        if payload.data.amount != booking.amount:
            webhook_record.status = "FAILED_AMOUNT_MISMATCH"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Webhook amount ({payload.data.amount}) does not match booking amount ({booking.amount})"
            )

        # Step 5: Protect terminal booking states
        if booking.status == BookingStatus.CONFIRMED.value:
            webhook_record.status = "IGNORED_ALREADY_CONFIRMED"
            db.commit()
            return WebhookResponse(
                status="ignored",
                message="Booking is already CONFIRMED; payment state preserved",
                event_id=payload.event_id,
            )

        if booking.status == BookingStatus.CANCELLED.value:
            webhook_record.status = "FAILED_BOOKING_CANCELLED"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot process payment for a CANCELLED booking"
            )

        # Step 6: Apply state transition and persist payment record
        outcome = payload.data.status.upper()
        if outcome == "SUCCESS":
            booking.status = BookingStatus.CONFIRMED.value
            payment_status = PaymentStatus.SUCCESS.value
        else:
            booking.status = BookingStatus.FAILED.value
            payment_status = PaymentStatus.FAILED.value

        payment = Payment(
            booking_id=booking.id,
            transaction_reference=payload.data.payment_reference,
            amount=payload.data.amount,
            status=payment_status,
            payment_method="WEBHOOK_GATEWAY",
        )
        db.add(payment)
        webhook_record.status = "PROCESSED"

        try:
            db.commit()
            return WebhookResponse(
                status="processed",
                message=f"Webhook processed: booking marked {booking.status}",
                event_id=payload.event_id,
            )
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error: payment reference or state conflict"
            )
