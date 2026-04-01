
def test_forgot_password_and_reset(
    client,
    register_user,
    verify_user,
    password_reset_code,
):
    from starlette import status
    email = "reset_test@example.com"
    old_password = "OldPassword123!"
    new_password = "NewPassword456!"

    register_user(email=email, password=old_password, first_name="Reset", last_name="User")
    verify_user(email)

    response = client.post("/forgot-password", json={"email": email})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "Password reset code sent to email"

    response = client.post(
        "/reset-password",
        json={"email": email, "code": password_reset_code, "new_password": new_password},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "Password has been reset successfully"

    login_response = client.post(
        "/login",
        data={"username": email, "password": new_password},
    )
    assert login_response.status_code == status.HTTP_200_OK
    assert "access_token" in login_response.json()


def test_forgot_password_non_existent_user(client):
    from starlette import status
    response = client.post("/forgot-password", json={"email": "nonexistent@example.com"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_reset_password_invalid_code(client, register_user):
    from starlette import status
    email = "invalid_code@example.com"
    register_user(email=email, password="Password123!", first_name="Invalid", last_name="Code")
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
