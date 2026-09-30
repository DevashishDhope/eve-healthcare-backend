import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal


def test_create_booking_success(client, auth_headers, sample_offering):
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    response = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": future_time
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["centre_test_id"] == str(sample_offering.id)
    assert data["status"] == "PENDING"
    assert float(data["amount"]) == float(sample_offering.price)


def test_price_snapshot_immutability(client, auth_headers, sample_offering, db_session):
    future_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    response = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": future_time
        }
    )
    assert response.status_code == 201
    booking_id = response.json()["id"]
    original_amount = float(response.json()["amount"])
    assert original_amount == 500.00

    # Simulate catalogue price increase for this offering
    sample_offering.price = Decimal("850.00")
    db_session.commit()

    # Retrieve existing booking - amount must still be the 500.00 historical snapshot!
    get_resp = client.get(f"/api/v1/bookings/{booking_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert float(get_resp.json()["amount"]) == 500.00


def test_create_booking_past_datetime_rejected(client, auth_headers, sample_offering):
    past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    response = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": past_time
        }
    )
    assert response.status_code == 422


def test_create_booking_nonexistent_offering(client, auth_headers):
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    random_id = uuid.uuid4()
    response = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(random_id),
            "appointment_datetime": future_time
        }
    )
    assert response.status_code == 404


def test_get_my_bookings(client, auth_headers, sample_offering):
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": future_time
        }
    )
    response = client.get("/api/v1/bookings", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_cancel_pending_booking(client, auth_headers, sample_offering):
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create_resp = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": future_time
        }
    )
    booking_id = create_resp.json()["id"]

    cancel_resp = client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=auth_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    # Attempting to cancel again should fail with 400
    second_cancel = client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=auth_headers)
    assert second_cancel.status_code == 400
