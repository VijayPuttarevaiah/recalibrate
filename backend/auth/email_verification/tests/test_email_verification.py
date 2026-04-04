from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

HTTP_OK = HTTP_200_OK
HTTP_BAD_REQUEST = HTTP_400_BAD_REQUEST
HTTP_NOT_FOUND = HTTP_404_NOT_FOUND


BASE_EMAIL = "verifyuser@example.com"
SECONDARY_EMAIL = "verifyuser2@example.com"
WRONG_CODE = "WRONG1"


def test_send_code_success(client, verification_code):
    response = client.post("/send-code", json={"email": BASE_EMAIL})
    assert response.status_code == HTTP_OK
    assert "Verification code sent" in response.json()["msg"]


def test_verify_success(client, register_user, verification_code):
    register_user(email=SECONDARY_EMAIL)
    client.post("/send-code", json={"email": SECONDARY_EMAIL})

    response = client.post(
        "/verify",
        json={"email": SECONDARY_EMAIL, "code": verification_code},
    )
    assert response.status_code == HTTP_OK
    assert response.json()["msg"] == "Email verified successfully"


def test_verify_wrong_code(client, register_user, verification_code):
    email = "wrongcode@example.com"
    register_user(email=email)
    client.post("/send-code", json={"email": email})

    response = client.post(
        "/verify",
        json={"email": email, "code": WRONG_CODE},
    )
    assert response.status_code == HTTP_BAD_REQUEST
    assert "Invalid verification code" in response.json()["detail"]


def test_verify_expired_code(client, register_user, verification_code, monkeypatch):
    email = "expiredcode@example.com"
    register_user(email=email)
    client.post("/send-code", json={"email": email})

    import auth.services.verification_service as verification_module

    expired_time = (
        verification_module.time.time() + verification_module.CODE_EXPIRY_SECONDS + 1
    )
    monkeypatch.setattr("auth.services.verification_service.time.time", lambda: expired_time)

    response = client.post(
        "/verify",
        json={"email": email, "code": verification_code},
    )
    assert response.status_code == HTTP_BAD_REQUEST
    assert "expired" in response.json()["detail"].lower()


def test_verify_no_code_sent(client, register_user):
    email = "nocodesent@example.com"
    register_user(email=email)
    response = client.post(
        "/verify",
        json={"email": email, "code": "ANY123"},
    )
    assert response.status_code == HTTP_NOT_FOUND
    assert "No code sent" in response.json()["detail"]


def test_verify_user_not_found(client, verification_code):
    email = "nouser@example.com"
    client.post("/send-code", json={"email": email})
    response = client.post(
        "/verify",
        json={"email": email, "code": verification_code},
    )
    assert response.status_code == HTTP_NOT_FOUND
    assert "User not found" in response.json()["detail"]
