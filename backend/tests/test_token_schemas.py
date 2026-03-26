"""
Test suite for token schemas (access token + refresh token responses).

Phase 1: TDD RED phase - Tests for token response schemas.
"""
import pytest
from pydantic import ValidationError
from schemas.token_schemas import Token, RefreshTokenResponse


class TestTokenSchema:
    """Test existing Token schema with access token."""
    
    def test_token_schema_valid(self):
        """Token schema should accept valid access token response."""
        token_data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user_id": 123
        }
        token = Token(**token_data)
        assert token.access_token == token_data["access_token"]
        assert token.token_type == "bearer"
        assert token.user_id == 123
    
    def test_token_schema_missing_access_token(self):
        """Token schema should require access_token."""
        with pytest.raises(ValidationError):
            Token(token_type="bearer", user_id=123)
    
    def test_token_schema_missing_user_id(self):
        """Token schema should require user_id."""
        with pytest.raises(ValidationError):
            Token(
                access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                token_type="bearer"
            )


class TestRefreshTokenSchema:
    """Test new refresh token response schema."""
    
    def test_refresh_token_response_valid(self):
        """RefreshTokenResponse should accept both tokens."""
        token_data = {
            "access_token": "new_access_jwt...",
            "refresh_token": "new_refresh_jwt...",
            "token_type": "bearer",
            "user_id": 123
        }
        response = RefreshTokenResponse(**token_data)
        assert response.access_token == "new_access_jwt..."
        assert response.refresh_token == "new_refresh_jwt..."
        assert response.token_type == "bearer"
        assert response.user_id == 123
    
    def test_refresh_token_response_missing_refresh_token(self):
        """RefreshTokenResponse should require refresh_token."""
        with pytest.raises(ValidationError):
            RefreshTokenResponse(
                access_token="new_access_jwt...",
                token_type="bearer",
                user_id=123
            )
    
    def test_refresh_token_response_missing_access_token(self):
        """RefreshTokenResponse should require access_token."""
        with pytest.raises(ValidationError):
            RefreshTokenResponse(
                refresh_token="new_refresh_jwt...",
                token_type="bearer",
                user_id=123
            )


class TestTokenRefreshRequest:
    """Test refresh request schema."""
    
    def test_token_refresh_request_valid(self):
        """TokenRefresh should accept refresh_token."""
        from schemas.token_schemas import TokenRefresh
        
        data = {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
        request = TokenRefresh(**data)
        assert request.refresh_token == data["refresh_token"]
    
    def test_token_refresh_request_missing_refresh_token(self):
        """TokenRefresh should require refresh_token."""
        from schemas.token_schemas import TokenRefresh
        
        with pytest.raises(ValidationError):
            TokenRefresh()


class TestLoginResponseIncludesRefreshToken:
    """Test that login response includes refresh token (modified Token schema)."""
    
    def test_login_response_has_refresh_token_field(self):
        """Login response should include refresh_token field."""
        token_data = {
            "access_token": "access_jwt...",
            "refresh_token": "refresh_jwt...",  # NEW
            "token_type": "bearer",
            "user_id": 123,
            "expires_in": 3600  # seconds until expiry
        }
        # This should not raise - Token schema should support refresh_token
        token = Token(**token_data)
        assert hasattr(token, "refresh_token")
        assert token.refresh_token == "refresh_jwt..."
    
    def test_login_response_has_expires_in(self):
        """Login response should include expires_in (seconds)."""
        token_data = {
            "access_token": "access_jwt...",
            "refresh_token": "refresh_jwt...",
            "token_type": "bearer",
            "user_id": 123,
            "expires_in": 3600
        }
        token = Token(**token_data)
        assert hasattr(token, "expires_in")
        assert token.expires_in == 3600
