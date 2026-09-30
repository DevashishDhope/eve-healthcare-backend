import uuid


def test_create_centre(client):
    response = client.post(
        "/api/v1/centres",
        json={"name": "Apollo Diagnostics", "location": "Koramangala, Bangalore"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Apollo Diagnostics"
    assert data["location"] == "Koramangala, Bangalore"
    assert "id" in data


def test_list_centres(client, sample_offering):
    response = client.get("/api/v1/centres")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(c["id"] == str(sample_offering.centre_id) for c in data)


def test_get_centre_by_id(client, sample_offering):
    response = client.get(f"/api/v1/centres/{sample_offering.centre_id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(sample_offering.centre_id)


def test_get_centre_not_found(client):
    random_id = uuid.uuid4()
    response = client.get(f"/api/v1/centres/{random_id}")
    assert response.status_code == 404


def test_create_test(client):
    response = client.post(
        "/api/v1/tests",
        json={"name": "Lipid Profile", "description": "Cholesterol and triglycerides check"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Lipid Profile"
    assert "id" in data


def test_list_tests(client, sample_offering):
    response = client.get("/api/v1/tests")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(t["id"] == str(sample_offering.test_id) for t in data)


def test_get_test_by_id(client, sample_offering):
    response = client.get(f"/api/v1/tests/{sample_offering.test_id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(sample_offering.test_id)


def test_get_test_not_found(client):
    random_id = uuid.uuid4()
    response = client.get(f"/api/v1/tests/{random_id}")
    assert response.status_code == 404


def test_create_centre_test_offering(client, sample_offering):
    # Create another test
    new_test_resp = client.post(
        "/api/v1/tests",
        json={"name": "Thyroid Profile", "description": "T3, T4, TSH panel"}
    )
    new_test_id = new_test_resp.json()["id"]

    response = client.post(
        "/api/v1/centre-tests",
        json={
            "centre_id": str(sample_offering.centre_id),
            "test_id": new_test_id,
            "price": 750.50
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert float(data["price"]) == 750.50
    assert data["centre_id"] == str(sample_offering.centre_id)
    assert data["test_id"] == new_test_id


def test_create_centre_test_duplicate_rejected(client, sample_offering):
    response = client.post(
        "/api/v1/centre-tests",
        json={
            "centre_id": str(sample_offering.centre_id),
            "test_id": str(sample_offering.test_id),
            "price": 600.00
        }
    )
    assert response.status_code == 400
    assert "already offered" in response.json()["detail"].lower()


def test_create_centre_test_nonexistent_centre(client, sample_offering):
    random_id = uuid.uuid4()
    response = client.post(
        "/api/v1/centre-tests",
        json={
            "centre_id": str(random_id),
            "test_id": str(sample_offering.test_id),
            "price": 500.00
        }
    )
    assert response.status_code == 404
    assert "centre not found" in response.json()["detail"].lower()


def test_create_centre_test_nonexistent_test(client, sample_offering):
    random_id = uuid.uuid4()
    response = client.post(
        "/api/v1/centre-tests",
        json={
            "centre_id": str(sample_offering.centre_id),
            "test_id": str(random_id),
            "price": 500.00
        }
    )
    assert response.status_code == 404
    assert "test not found" in response.json()["detail"].lower()


def test_get_centre_test_by_id(client, sample_offering):
    response = client.get(f"/api/v1/centre-tests/{sample_offering.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_offering.id)
    assert float(data["price"]) == 500.00
    assert data["centre"]["name"] == sample_offering.centre.name
    assert data["test"]["name"] == sample_offering.test.name
