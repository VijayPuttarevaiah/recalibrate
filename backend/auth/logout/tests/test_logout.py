from auth.models.token_models import BlacklistedToken

HTTP_UNAUTHORIZED = 401
HTTP_OK = 200

class TestLogout:
    """Test cases for /logout endpoint."""

    token = "fake_token_123"
    blacklisted_token_value = "already_blacklisted_token"

    def test_logout_success(self, client, db_session):
        headers = {"Authorization": f"Bearer {self.token}"}

        response = client.post("/logout", headers=headers)

        assert response.status_code == HTTP_OK
        assert response.json() == {"msg": "Successfully logged out"}

        blacklisted = (
            db_session.query(BlacklistedToken)
            .filter(BlacklistedToken.token == self.token)
            .first()
        )
        assert blacklisted is not None
        assert blacklisted.token == self.token

    def test_logout_blacklisted(self, client, db_session):
        blacklisted_token = BlacklistedToken(token=self.blacklisted_token_value)
        db_session.add(blacklisted_token)
        db_session.commit()

        headers = {"Authorization": f"Bearer {self.blacklisted_token_value}"}

        response = client.post("/logout", headers=headers)

        assert response.status_code == HTTP_OK
        assert response.json() == {"msg": "Token already blacklisted"}

    def test_logout_no_auth_header(self, client):
        response = client.post("/logout")

        assert response.status_code == HTTP_UNAUTHORIZED
