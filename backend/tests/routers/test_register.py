# Test cases for the user registration endpoint (/register)
import pytest

# Test that a new user can register successfully with valid details
def test_register_success(client):
    response = client.post("/register", json={
        "email": "testuser2@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "StrongPassword123"
    })
    assert response.status_code == 200
    assert "User registered successfully" in response.json()["msg"]

# Test that registering with an email that already exists returns an error
def test_register_duplicate_email(client):
    # First registration attempt
    client.post("/register", json={
        "email": "duplicate@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "Password1"
    })
    # Second registration attempt with the same email
    response = client.post("/register", json={
        "email": "duplicate@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "Password1"
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

# Test that registration fails if the email format is invalid
def test_register_invalid_email(client):
    response = client.post("/register", json={
        "email": "not-an-email",
        "first_name": "Test",
        "last_name": "User",
        "password": "Password1"
    })
    assert response.status_code == 422

# Test that registration fails if required fields are missing from the request
def test_register_missing_fields(client):
    response = client.post("/register", json={
        "email": "missingfields@example.com",
        "password": "Password1"
    })
    assert response.status_code == 422

# Test registration behavior with a short or weak password
def test_register_weak_password(client):
    response = client.post("/register", json={
        "email": "weakpass@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "123"
    })
    assert response.status_code in (200, 400, 422)
