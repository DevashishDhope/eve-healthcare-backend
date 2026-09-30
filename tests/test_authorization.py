from datetime import datetime, timedelta, timezone


def test_cross_user_access_forbidden(client, auth_headers, auth_headers_user_2, sample_offering):
    # User 1 creates a booking
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create_resp = client.post(
        "/api/v1/bookings",
        headers=auth_headers,
        json={
            "centre_test_id": str(sample_offering.id),
            "appointment_datetime": future_time
        }
    )
    assert create_resp.status_code == 201
    booking_id = create_resp.json()["id"]

    # User 2 tries to view User 1's booking
    get_resp = client.get(f"/api/v1/bookings/{booking_id}", headers=auth_headers_user_2)
    assert get_resp.status_code == 403
    assert "permission" in get_resp.json()["detail"].lower()

    # User 2 tries to cancel User 1's booking
    cancel_resp = client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=auth_headers_user_2)
    assert cancel_resp.status_code == 403

    # User 2 tries to pay for User 1's booking
    pay_resp = client.post(
        "/api/v1/payments",
        headers=auth_headers_user_2,
        json={
            "booking_id": booking_id,
            "simulate_outcome": "SUCCESS"
        }
    )
    assert pay_resp.status_code == 403
