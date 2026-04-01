import pytest
from models.token_models import BlacklistedToken

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401

def test_logout_success(client, db_session):
    """
    Test that a valid token is successfully added to the blacklist on logout.
    """
    # Prepare: Create a mock token and authorization header
    token = "fake_token_123"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Execute: Send a POST request to the /logout endpoint
    response = client.post("/logout", headers=headers)
    
    # Assert: Verify the response status and message
    assert response.status_code == HTTP_OK
    assert response.json() == {"msg": "Successfully logged out"}
    
    # Verify: Check if the token was actually saved in the BlacklistedToken table
    blacklisted = db_session.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
    assert blacklisted is not None
    assert blacklisted.token == token

def test_logout_already_blacklisted(client, db_session):
    """
    Test that attempting to logout with an already blacklisted token is handled gracefully.
    """
    # Prepare: Manually add a token to the blacklist in the test database
    token = "already_blacklisted_token"
    blacklisted_token = BlacklistedToken(token=token)
    db_session.add(blacklisted_token)
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Execute: Call logout again with the same token
    response = client.post("/logout", headers=headers)
    
    # Assert: Verify the informative message returned
    assert response.status_code == HTTP_OK
    assert response.json() == {"msg": "Token already blacklisted"}

def test_logout_no_auth_header(client):
    """
    Test that logout fails if no Authorization header is provided.
    """
    # Execute: Send request without any authentication headers
    response = client.post("/logout")
    
    # Assert: FastAPI's OAuth2PasswordBearer should automatically return 401 Unauthorized
    assert response.status_code == HTTP_UNAUTHORIZED
