def test_signup_success(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "newpatient@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newpatient@example.com"
    assert "id" in data
    assert "password_hash" not in data
    assert "password" not in data


def test_signup_duplicate_email(client, test_user):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": test_user.email, "password": "anotherpassword"}
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_signup_invalid_email(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "not-an-email", "password": "validpassword123"}
    )
    assert response.status_code == 422


def test_signup_short_password(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "shortpw@example.com", "password": "123"}
    )
    assert response.status_code == 422


def test_login_success(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user.email


def test_login_invalid_password(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "password123"}
    )
    assert response.status_code == 401


def test_get_me_authenticated(client, auth_headers, test_user):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email


def test_get_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert response.status_code == 401
