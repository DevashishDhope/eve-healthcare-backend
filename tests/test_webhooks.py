from datetime import datetime, timedelta, timezone
from app.core.config import settings
from app.models.payment import Payment

WEBHOOK_HEADERS = {"X-Webhook-Secret": settings.WEBHOOK_SECRET}


def test_webhook_success_confirms_booking(client, auth_headers, sample_offering):
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

    webhook_payload = {
        "event_id": "evt_test_001",
        "event_type": "payment.succeeded",
        "data": {
            "booking_id": booking_id,
            "payment_reference": "TXN_EXT_001",
            "status": "SUCCESS",
            "amount": 500.00
        }
    }

    response = client.post("/api/v1/payments/webhook", json=webhook_payload, headers=WEBHOOK_HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "processed"

    # Verify booking status became CONFIRMED
    get_booking = client.get(f"/api/v1/bookings/{booking_id}", headers=auth_headers)
    assert get_booking.json()["status"] == "CONFIRMED"


def test_webhook_failed_marks_booking_failed(client, auth_headers, sample_offering):
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

    webhook_payload = {
        "event_id": "evt_test_fail_002",
        "event_type": "payment.failed",
        "data": {
            "booking_id": booking_id,
            "payment_reference": "TXN_EXT_FAIL_002",
            "status": "FAILED",
            "amount": 500.00
        }
    }

    response = client.post("/api/v1/payments/webhook", json=webhook_payload, headers=WEBHOOK_HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "processed"

    # Verify booking status became FAILED
    get_booking = client.get(f"/api/v1/bookings/{booking_id}", headers=auth_headers)
    assert get_booking.json()["status"] == "FAILED"


def test_webhook_idempotency_duplicate_event(client, auth_headers, sample_offering, db_session):
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

    webhook_payload = {
        "event_id": "evt_idempotency_003",
        "event_type": "payment.succeeded",
        "data": {
            "booking_id": booking_id,
            "payment_reference": "TXN_EXT_003",
            "status": "SUCCESS",
            "amount": 500.00
        }
    }

    # First webhook submission
    resp1 = client.post("/api/v1/payments/webhook", json=webhook_payload, headers=WEBHOOK_HEADERS)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "processed"

    # Second submission with the exact same event_id
    resp2 = client.post("/api/v1/payments/webhook", json=webhook_payload, headers=WEBHOOK_HEADERS)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "ignored"
    assert "duplicate" in resp2.json()["message"].lower()

    # Verify database has exactly 1 payment record for this booking
    payments = db_session.query(Payment).filter(Payment.booking_id == booking_id).all()
    assert len(payments) == 1


def test_webhook_unauthorized_missing_secret(client):
    webhook_payload = {
        "event_id": "evt_test_unauth",
        "data": {
            "booking_id": "00000000-0000-0000-0000-000000000000",
            "payment_reference": "TXN_0",
            "status": "SUCCESS",
            "amount": 100.00
        }
    }
    response = client.post("/api/v1/payments/webhook", json=webhook_payload)
    assert response.status_code == 401


def test_webhook_unauthorized_invalid_secret(client):
    webhook_payload = {
        "event_id": "evt_test_invalid_secret",
        "data": {
            "booking_id": "00000000-0000-0000-0000-000000000000",
            "payment_reference": "TXN_0",
            "status": "SUCCESS",
            "amount": 100.00
        }
    }
    response = client.post(
        "/api/v1/payments/webhook",
        json=webhook_payload,
        headers={"X-Webhook-Secret": "wrong_secret"}
    )
    assert response.status_code == 401


def test_webhook_amount_mismatch_rejected(client, auth_headers, sample_offering):
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

    webhook_payload = {
        "event_id": "evt_mismatch_004",
        "event_type": "payment.succeeded",
        "data": {
            "booking_id": booking_id,
            "payment_reference": "TXN_EXT_004",
            "status": "SUCCESS",
            "amount": 10.00  # Incorrect amount (actual is 500.00)
        }
    }

    response = client.post("/api/v1/payments/webhook", json=webhook_payload, headers=WEBHOOK_HEADERS)
    assert response.status_code == 400
    assert "amount" in response.json()["detail"].lower()

    # Ensure booking remained PENDING
    get_booking = client.get(f"/api/v1/bookings/{booking_id}", headers=auth_headers)
    assert get_booking.json()["status"] == "PENDING"


def test_webhook_cancelled_booking_protected(client, auth_headers, sample_offering):
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
    client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=auth_headers)

    webhook_payload = {
        "event_id": "evt_cancelled_005",
        "event_type": "payment.succeeded",
        "data": {
            "booking_id": booking_id,
            "payment_reference": "TXN_EXT_005",
            "status": "SUCCESS",
            "amount": 500.00
        }
    }

    response = client.post("/api/v1/payments/webhook", json=webhook_payload, headers=WEBHOOK_HEADERS)
    assert response.status_code == 400
    assert "cancelled" in response.json()["detail"].lower()

    # Ensure booking is still CANCELLED
    get_booking = client.get(f"/api/v1/bookings/{booking_id}", headers=auth_headers)
    assert get_booking.json()["status"] == "CANCELLED"
