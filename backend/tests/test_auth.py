"""Tests for user registration, login, and JWT authentication."""


def test_register_user(client):
    """Test successful user registration."""
    payload = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "SecurePassword123!",
        "full_name": "New User",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["username"] == "newuser"


def test_register_duplicate_email(client, test_user):
    """Ensure duplicate email registration is rejected with HTTP 400."""
    payload = {
        "email": test_user.email,
        "username": "distinctusername",
        "password": "Password123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_register_duplicate_username(client, test_user):
    """Ensure duplicate username registration is rejected with HTTP 400."""
    payload = {
        "email": "unique@example.com",
        "username": test_user.username,
        "password": "Password123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"]


def test_login_successful(client, test_user):
    """Test login with valid username and password."""
    payload = {
        "username_or_email": test_user.username,
        "password": "Password123!",
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_email(client, test_user):
    """Test login with email instead of username."""
    payload = {
        "username_or_email": test_user.email,
        "password": "Password123!",
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200


def test_login_invalid_password(client, test_user):
    """Test login fails with incorrect password."""
    payload = {
        "username_or_email": test_user.username,
        "password": "WrongPassword!",
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401


def test_get_profile_authenticated(client, auth_headers, test_user):
    """Test accessing protected /auth/me with valid Bearer token."""
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


def test_get_profile_unauthenticated(client):
    """Test accessing protected /auth/me without token fails with 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
