from starlette.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

HTTP_CREATED = HTTP_201_CREATED
HTTP_BAD_REQUEST = HTTP_400_BAD_REQUEST
HTTP_UNPROCESSABLE = HTTP_422_UNPROCESSABLE_ENTITY


EMAIL = "testuser2@example.com"
PASSWORD = "StrongPassword123!"


def test_register_success(register_user):
    response = register_user(email=EMAIL, password=PASSWORD)
    assert response.status_code == HTTP_CREATED
    assert response.json()["msg"] == "User registered successfully"


def test_register_duplicate_email(register_user):
    duplicate_email = "duplicate@example.com"
    register_user(email=duplicate_email, password="Password1!")
    response = register_user(email=duplicate_email, password="Password1!")
    assert response.status_code == HTTP_BAD_REQUEST
    assert "already registered" in response.json()["detail"]


def test_register_invalid_email(register_user):
    response = register_user(email="not-an-email", password="Password1!")
    assert response.status_code == HTTP_UNPROCESSABLE


def test_register_missing_fields(client):
    response = client.post(
        "/register",
        json={"email": "missingfields@example.com", "password": "Password1!"},
    )
    assert response.status_code == HTTP_UNPROCESSABLE


def test_register_weak_password(register_user):
    response = register_user(email="weakpass@example.com", password="123")
    assert response.status_code == HTTP_CREATED
    assert response.json()["msg"] == "User registered successfully"
