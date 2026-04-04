from auth.models.token_models import BlacklistedToken

HTTP_UNAUTHORIZED = 401
HTTP_OK = 200


TOKEN = "fake_token_123"
BLACKLISTED_TOKEN_VALUE = "already_blacklisted_token"


def test_logout_success(client, db_session):
    headers = {"Authorization": f"Bearer {TOKEN}"}

    response = client.post("/logout", headers=headers)

    assert response.status_code == HTTP_OK
    assert response.json() == {"msg": "Successfully logged out"}

    blacklisted = (
        db_session.query(BlacklistedToken).filter(BlacklistedToken.token == TOKEN).first()
    )
    assert blacklisted is not None
    assert blacklisted.token == TOKEN


def test_logout_blacklisted(client, db_session):
    blacklisted_token = BlacklistedToken(token=BLACKLISTED_TOKEN_VALUE)
    db_session.add(blacklisted_token)
    db_session.commit()

    headers = {"Authorization": f"Bearer {BLACKLISTED_TOKEN_VALUE}"}

    response = client.post("/logout", headers=headers)

    assert response.status_code == HTTP_OK
    assert response.json() == {"msg": "Token already blacklisted"}


def test_logout_no_auth_header(client):
    response = client.post("/logout")

    assert response.status_code == HTTP_UNAUTHORIZED
