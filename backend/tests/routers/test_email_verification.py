# Test cases for email verification endpoints (/send-code and /verify)
import pytest
import time

# Test that a verification code is successfully sent to the user's email
def test_send_code_success(client):
    response = client.post("/send-code", json={"email": "verifyuser@example.com"})
    assert response.status_code == 200
    assert "Verification code sent" in response.json()["msg"]

# Test that a user can successfully verify their email with the correct code
def test_verify_success(client, monkeypatch):
    email = "verifyuser2@example.com"
    # Step 1: Request a verification code
    client.post("/send-code", json={"email": email})
    # Step 2: Retrieve the code from the in-memory store for testing purposes
    from routers import email_verification
    code, _ = email_verification.verification_codes[email]
    # Step 3: Register the user
    client.post("/register", json={
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "password": "Password123"
    })
    # Step 4: Verify the email using the retrieved code
    response = client.post("/verify", json={"email": email, "code": code})
    assert response.status_code in (200, 204)

# Test that verification fails when an incorrect code is provided
def test_verify_wrong_code(client):
    email = "wrongcode@example.com"
    client.post("/send-code", json={"email": email})
    client.post("/register", json={
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "password": "Password123"
    })
    response = client.post("/verify", json={"email": email, "code": "WRONG1"})
    assert response.status_code == 400
    assert "Invalid verification code" in response.json()["detail"]

# Test that verification fails when the code has expired
def test_verify_expired_code(client, monkeypatch):
    email = "expiredcode@example.com"
    client.post("/send-code", json={"email": email})
    from routers import email_verification
    code, expiry = email_verification.verification_codes[email]
    # Manually set the expiry time to the past
    email_verification.verification_codes[email] = (code, time.time() - 1)
    client.post("/register", json={
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "password": "Password123"
    })
    response = client.post("/verify", json={"email": email, "code": code})
    assert response.status_code == 400
    assert "expired" in response.json()["detail"]

# Test verification attempt for an email that was never sent a code
def test_verify_no_code_sent(client):
    email = "nocodesent@example.com"
    client.post("/register", json={
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "password": "Password123"
    })
    response = client.post("/verify", json={"email": email, "code": "ANY123"})
    assert response.status_code == 404
    assert "No code sent" in response.json()["detail"]

# Test verification attempt for a code sent to an email not yet registered
def test_verify_user_not_found(client):
    email = "nouser@example.com"
    client.post("/send-code", json={"email": email})
    from routers import email_verification
    code, _ = email_verification.verification_codes[email]
    response = client.post("/verify", json={"email": email, "code": code})
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
