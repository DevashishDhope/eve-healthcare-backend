import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from app.models.payment import Payment, PaymentStatus


def test_simulate_payment_success(client, auth_headers, sample_offering):
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    booking_resp = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": future_time
        }
    )
    booking_id = booking_resp.json()["id"]

    pay_resp = client.post(
        "/api/v1/payments",
        headers=auth_headers,
        json={
            "booking_id": booking_id,
            "simulate_outcome": "SUCCESS"
        }
    )
    assert pay_resp.status_code == 200
    payment_data = pay_resp.json()
    assert payment_data["status"] == "SUCCESS"
    assert payment_data["booking_id"] == booking_id
    assert float(payment_data["amount"]) == float(sample_offering.price)
    assert "transaction_reference" in payment_data

    # Verify booking status changed to CONFIRMED
    get_booking = client.get(f"/api/v1/bookings/{booking_id}", headers=auth_headers)
    assert get_booking.json()["status"] == "CONFIRMED"


def test_simulate_payment_failed(client, auth_headers, sample_offering):
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    booking_resp = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": future_time
        }
    )
    booking_id = booking_resp.json()["id"]

    pay_resp = client.post(
        "/api/v1/payments",
        headers=auth_headers,
        json={
            "booking_id": booking_id,
            "simulate_outcome": "FAILED"
        }
    )
    assert pay_resp.status_code == 200
    assert pay_resp.json()["status"] == "FAILED"

    # Verify booking status changed to FAILED
    get_booking = client.get(f"/api/v1/bookings/{booking_id}", headers=auth_headers)
    assert get_booking.json()["status"] == "FAILED"


def test_duplicate_payment_on_confirmed_booking_rejected(client, auth_headers, sample_offering):
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    booking_resp = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": future_time
        }
    )
    booking_id = booking_resp.json()["id"]

    # First payment succeeds
    pay_resp_1 = client.post(
        "/api/v1/payments",
        headers=auth_headers,
        json={"booking_id": booking_id, "simulate_outcome": "SUCCESS"}
    )
    assert pay_resp_1.status_code == 200

    # Second payment must be rejected
    pay_resp_2 = client.post(
        "/api/v1/payments",
        headers=auth_headers,
        json={"booking_id": booking_id, "simulate_outcome": "SUCCESS"}
    )
    assert pay_resp_2.status_code == 400
    assert "already confirmed" in pay_resp_2.json()["detail"].lower()


def test_payment_on_cancelled_booking_rejected(client, auth_headers, sample_offering):
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    booking_resp = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": future_time
        }
    )
    booking_id = booking_resp.json()["id"]

    # Cancel booking
    cancel_resp = client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=auth_headers)
    assert cancel_resp.status_code == 200

    # Attempt payment on cancelled booking
    pay_resp = client.post(
        "/api/v1/payments",
        headers=auth_headers,
        json={"booking_id": booking_id, "simulate_outcome": "SUCCESS"}
    )
    assert pay_resp.status_code == 400
    assert "cancelled" in pay_resp.json()["detail"].lower()


def test_postgresql_partial_unique_index_enforcement(client, auth_headers, sample_offering, db_session):
    """Directly verifies PostgreSQL partial unique index uq_one_success_payment_per_booking."""
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    booking_resp = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": future_time
        }
    )
    booking_id = booking_resp.json()["id"]

    # Insert first SUCCESS payment
    p1 = Payment(
        booking_id=booking_id,
        transaction_reference="TXN_TEST_001",
        amount=500.00,
        status=PaymentStatus.SUCCESS.value,
        payment_method="TEST"
    )
    db_session.add(p1)
    db_session.commit()

    # Attempt to insert second SUCCESS payment directly in DB bypassing app logic
    p2 = Payment(
        booking_id=booking_id,
        transaction_reference="TXN_TEST_002",
        amount=500.00,
        status=PaymentStatus.SUCCESS.value,
        payment_method="TEST"
    )
    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
