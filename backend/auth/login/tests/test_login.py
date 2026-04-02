class TestLogin:
    """Test cases for /login endpoint."""

    email = "loginuser@example.com"
    password = "Password123!"
    wrong_password = "WrongPassword"

    def test_login_success(self, client, register_user, verify_user):
        register_user(email=self.email, password=self.password)
        verify_user(self.email)

        response = client.post(
            "/login",
            data={"username": self.email, "password": self.password},
        )
        assert response.status_code == HTTP_OK
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client, register_user, verify_user):
        email = "wrongpass@example.com"
        register_user(email=email, password=self.password)
        verify_user(email)

        response = client.post(
            "/login",
            data={"username": email, "password": self.wrong_password},
        )
        assert response.status_code == HTTP_BAD_REQUEST
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_unverified_email(self, client, register_user):
        email = "unverified@example.com"
        register_user(email=email, password=self.password)

        response = client.post(
            "/login",
            data={"username": email, "password": self.password},
        )
        assert response.status_code == HTTP_FORBIDDEN
        assert "Email not verified" in response.json()["detail"]

    def test_login_missing_fields(self, client):
        response = client.post(
            "/login",
            data={"username": "missingpass@example.com"},
        )
        assert response.status_code == HTTP_UNPROCESSABLE

    def test_login_empty_credentials(self, client):
        response = client.post(
            "/login",
            data={"username": "", "password": ""},
        )

        assert response.status_code in (HTTP_BAD_REQUEST, HTTP_UNPROCESSABLE)

    def test_login_invalid_email(self, client):
        response = client.post(
            "/login",
            data={"username": "notanemail", "password": self.password},
        )
        # Should return 400 or 422 depending on how pydantic/fastapi handles the error
        assert response.status_code in (HTTP_BAD_REQUEST, HTTP_UNPROCESSABLE)
