def test_forgot_password_and_reset(
    client,
    register_user,
    verify_user,
    password_reset_code,
):
    email = "reset_test@example.com"
    old_password = "oldpassword123"
    new_password = "newpassword456"

    register_user(email=email, password=old_password, first_name="Reset", last_name="User")
    verify_user(email)

    response = client.post("/forgot-password", json={"email": email})
    assert response.status_code == 200
    assert response.json()["msg"] == "Password reset code sent to email"

    response = client.post(
        "/reset-password",
        json={"email": email, "code": password_reset_code, "new_password": new_password},
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "Password has been reset successfully"

    login_response = client.post(
        "/login",
        data={"username": email, "password": new_password},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_forgot_password_non_existent_user(client):
    response = client.post("/forgot-password", json={"email": "nonexistent@example.com"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_reset_password_invalid_code(client, register_user):
    email = "invalid_code@example.com"
    register_user(email=email, password="password123", first_name="Invalid", last_name="Code")
    client.post("/forgot-password", json={"email": email})

    response = client.post(
        "/reset-password",
        json={
            "email": email,
            "code": "WRONGCODE",
            "new_password": "newpassword123",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid reset code"
