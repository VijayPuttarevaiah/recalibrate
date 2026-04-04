"""Test cases for password reset endpoints."""


EMAIL = "reset_test@example.com"
OLD_PASSWORD = "OldPassword123!"
NEW_PASSWORD = "NewPassword456!"


def test_forgot_password_and_reset(
    client,
    register_user,
    verify_user,
    password_reset_code,
):
    from starlette import status

    register_user(
        email=EMAIL,
        password=OLD_PASSWORD,
        first_name="Reset",
        last_name="User",
    )
    verify_user(EMAIL)

    response = client.post("/forgot-password", json={"email": EMAIL})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "Password reset code sent to email"

    response = client.post(
        "/reset-password",
        json={
            "email": EMAIL,
            "code": password_reset_code,
            "new_password": NEW_PASSWORD,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "Password has been reset successfully"

    login_response = client.post(
        "/login",
        data={"username": EMAIL, "password": NEW_PASSWORD},
    )
    assert login_response.status_code == status.HTTP_200_OK
    assert "access_token" in login_response.json()


def test_forgot_pwd_missing_user(client):
    from starlette import status

    response = client.post(
        "/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_reset_password_bad_code(client, register_user):
    from starlette import status

    email = "invalid_code@example.com"
    register_user(
        email=email,
        password="Password123!",
        first_name="Invalid",
        last_name="Code",
    )
    client.post("/forgot-password", json={"email": email})

    response = client.post(
        "/reset-password",
        json={
            "email": email,
            "code": "WRONGCODE",
            "new_password": "NewPassword123!",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid reset code"
