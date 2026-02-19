# Test cases for the user registration endpoint (/register)


def test_register_success(register_user):
    response = register_user(email="testuser2@example.com", password="StrongPassword123")
    assert response.status_code == 201
    assert response.json()["msg"] == "User registered successfully"


def test_register_duplicate_email(register_user):
    register_user(email="duplicate@example.com", password="Password1")
    response = register_user(email="duplicate@example.com", password="Password1")
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_register_invalid_email(register_user):
    response = register_user(email="not-an-email", password="Password1")
    assert response.status_code == 422


def test_register_missing_fields(client):
    response = client.post(
        "/register",
        json={"email": "missingfields@example.com", "password": "Password1"},
    )
    assert response.status_code == 422


def test_register_weak_password(register_user):
    response = register_user(email="weakpass@example.com", password="123")
    assert response.status_code == 201
    assert response.json()["msg"] == "User registered successfully"
