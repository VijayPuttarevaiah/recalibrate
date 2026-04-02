HTTP_CREATED = 201


class TestRegister:
    """Test cases for the user registration endpoint (/register)."""

    email = "testuser2@example.com"
    password = "StrongPassword123!"

    def test_register_success(self, register_user):
        response = register_user(email=self.email, password=self.password)
        assert response.status_code == HTTP_CREATED
        assert response.json()["msg"] == "User registered successfully"

    def test_register_duplicate_email(self, register_user):
        duplicate_email = "duplicate@example.com"
        register_user(email=duplicate_email, password="Password1!")
        response = register_user(email=duplicate_email, password="Password1!")
        assert response.status_code == HTTP_BAD_REQUEST
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_email(self, register_user):
        response = register_user(email="not-an-email", password="Password1!")
        assert response.status_code == HTTP_UNPROCESSABLE

    def test_register_missing_fields(self, client):
        response = client.post(
            "/register",
            json={"email": "missingfields@example.com", "password": "Password1!"},
        )
        assert response.status_code == HTTP_UNPROCESSABLE

    def test_register_weak_password(self, register_user):
        response = register_user(email="weakpass@example.com", password="123")
        assert response.status_code == HTTP_CREATED
        assert response.json()["msg"] == "User registered successfully"
