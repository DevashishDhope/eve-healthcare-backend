import uuid
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.models.centre_test import CentreTest
from app.schemas.booking import BookingCreate


class BookingService:
    @staticmethod
    def create_booking(db: Session, user_id: uuid.UUID, booking_data: BookingCreate) -> Booking:
        centre_test = db.query(CentreTest).filter(CentreTest.id == booking_data.centre_test_id).first()
        if not centre_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Centre-Test offering not found"
            )

        booking = Booking(
            user_id=user_id,
            centre_test_id=centre_test.id,
            appointment_datetime=booking_data.appointment_datetime,
            amount=centre_test.price,  # Historical price snapshot
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def get_user_bookings(db: Session, user_id: uuid.UUID) -> List[Booking]:
        return db.query(Booking).filter(Booking.user_id == user_id).order_by(Booking.created_at.desc()).all()

    @staticmethod
    def get_booking_by_id(db: Session, booking_id: uuid.UUID, user_id: uuid.UUID) -> Booking:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        if booking.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this booking"
            )
        return booking

    @staticmethod
    def cancel_booking(db: Session, booking_id: uuid.UUID, user_id: uuid.UUID) -> Booking:
        booking = BookingService.get_booking_by_id(db, booking_id, user_id)
        if booking.status != BookingStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel booking with status '{booking.status}'. Only PENDING bookings can be cancelled."
            )
        booking.status = BookingStatus.CANCELLED.value
        db.commit()
        db.refresh(booking)
        return booking
