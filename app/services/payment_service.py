import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import SimulatedPaymentRequest


class PaymentService:
    @staticmethod
    def process_simulated_payment(
        db: Session, user_id: uuid.UUID, payment_req: SimulatedPaymentRequest
    ) -> Payment:
        # Row-level locking to serialize concurrent payment attempts on the booking
        booking = (
            db.query(Booking)
            .filter(Booking.id == payment_req.booking_id)
            .with_for_update()
            .first()
        )
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
            
        if booking.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to pay for this booking"
            )

        if booking.status == BookingStatus.CONFIRMED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking is already confirmed and paid"
            )

        if booking.status == BookingStatus.CANCELLED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot process payment for a cancelled booking"
            )

        # Ensure no existing successful payment exists
        existing_success = (
            db.query(Payment)
            .filter(
                Payment.booking_id == booking.id,
                Payment.status == PaymentStatus.SUCCESS.value
            )
            .first()
        )
        if existing_success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A successful payment already exists for this booking"
            )

        outcome = payment_req.simulate_outcome.upper()
        txn_ref = f"TXN_SIM_{uuid.uuid4().hex[:12].upper()}"

        if outcome == PaymentStatus.SUCCESS.value:
            payment_status = PaymentStatus.SUCCESS.value
            booking.status = BookingStatus.CONFIRMED.value
        else:
            payment_status = PaymentStatus.FAILED.value
            booking.status = BookingStatus.FAILED.value

        payment = Payment(
            booking_id=booking.id,
            transaction_reference=txn_ref,
            amount=booking.amount,
            status=payment_status,
            payment_method=payment_req.payment_method,
        )
        db.add(payment)

        try:
            db.commit()
            db.refresh(payment)
            return payment
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment constraint violation: a successful payment may already exist"
            )
