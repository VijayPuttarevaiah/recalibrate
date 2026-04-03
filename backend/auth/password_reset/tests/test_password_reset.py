class TestPasswordReset:
    """Test cases for password reset endpoints."""

    email = "reset_test@example.com"
    old_password = "OldPassword123!"
    new_password = "NewPassword456!"

    def test_forgot_password_and_reset(
        self,
        client,
        register_user,
        verify_user,
        password_reset_code,
    ):
        from starlette import status

        register_user(
            email=self.email,
            password=self.old_password,
            first_name="Reset",
            last_name="User",
        )
        verify_user(self.email)

        response = client.post("/forgot-password", json={"email": self.email})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["msg"] == "Password reset code sent to email"

        response = client.post(
            "/reset-password",
            json={
                "email": self.email,
                "code": password_reset_code,
                "new_password": self.new_password,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["msg"] == "Password has been reset successfully"

        login_response = client.post(
            "/login",
            data={"username": self.email, "password": self.new_password},
        )
        assert login_response.status_code == status.HTTP_200_OK
        assert "access_token" in login_response.json()

    def test_forgot_pwd_missing_user(self, client):
        from starlette import status

        response = client.post(
            "/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "User not found"

    def test_reset_password_bad_code(self, client, register_user):
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
