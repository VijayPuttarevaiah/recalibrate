"""
Tests for Auth Service Refresh Token Methods
Tests refreshing access tokens using valid refresh tokens, token rotation, and error cases
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from services.auth_service import AuthService
from models.user_models import User
from models.token_models import RefreshToken
from schemas.token_schemas import TokenRefresh


@pytest.fixture
def mock_db():
    """Mock database session"""
    return MagicMock()


@pytest.fixture
def mock_user():
    """Mock user object"""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.password = "hashed_password"
    user.is_verified = True
    return user


@pytest.fixture
def mock_refresh_token():
    """Mock refresh token object that's valid (not revoked, not expired)"""
    token = MagicMock(spec=RefreshToken)
    token.id = 1
    token.user_id = 1
    token.token_hash = "token_hash"
    token.expires_at = datetime.now(timezone.utc) + timedelta(days=6)
    token.created_at = datetime.now(timezone.utc)
    token.is_revoked = False
    token.is_valid = MagicMock(return_value=True)
    token.is_expired = MagicMock(return_value=False)
    return token


@pytest.fixture
def auth_service(mock_db):
    """Create AuthService instance with mocked db"""
    return AuthService(mock_db)


class TestHashToken:
    """Test token hashing utility"""

    def test_hash_token_creates_sha256_hash(self, auth_service):
        """Test that _hash_token creates SHA256 hash of token"""
        token = "test_token_string"
        hash_result = auth_service._hash_token(token)
        
        # Should be 64 character hex string (SHA256)
        assert len(hash_result) == 64
        assert isinstance(hash_result, str)
    
    def test_hash_token_is_deterministic(self, auth_service):
        """Test that hashing same token twice gives same result"""
        token = "test_token_string"
        hash1 = auth_service._hash_token(token)
        hash2 = auth_service._hash_token(token)
        
        assert hash1 == hash2
    
    def test_hash_different_tokens_gives_different_hashes(self, auth_service):
        """Test that different tokens produce different hashes"""
        hash1 = auth_service._hash_token("token1")
        hash2 = auth_service._hash_token("token2")
        
        assert hash1 != hash2


class TestGenerateRefreshToken:
    """Test refresh token generation"""

    def test_generate_refresh_token_returns_string(self, auth_service):
        """Test that _generate_refresh_token returns a string"""
        token = auth_service._generate_refresh_token()
        assert isinstance(token, str)
    
    def test_generate_refresh_token_creates_random_values(self, auth_service):
        """Test that generated tokens are unique (random)"""
        token1 = auth_service._generate_refresh_token()
        token2 = auth_service._generate_refresh_token()
        
        assert token1 != token2
    
    def test_generate_refresh_token_has_sufficient_length(self, auth_service):
        """Test that generated tokens have sufficient entropy"""
        token = auth_service._generate_refresh_token()
        
        # secrets.token_urlsafe(64) produces approximately 85 character string
        assert len(token) >= 80


class TestCreateRefreshToken:
    """Test creating and storing refresh tokens"""

    def test_create_refresh_token_returns_token_and_hash(self, auth_service):
        """Test that create_refresh_token returns tuple of token and hash"""
        token, token_hash = auth_service.create_refresh_token(user_id=1)
        
        assert isinstance(token, str)
        assert isinstance(token_hash, str)
        assert len(token) >= 80
        assert len(token_hash) == 64
    
    def test_create_refresh_token_calls_repository(self, auth_service, mock_db):
        """Test that create_refresh_token persists token to database"""
        auth_service.token_repo.create_refresh_token = MagicMock()
        
        token, token_hash = auth_service.create_refresh_token(user_id=1)
        
        # Verify repository method was called with correct parameters
        auth_service.token_repo.create_refresh_token.assert_called_once()
        call_args = auth_service.token_repo.create_refresh_token.call_args
        
        assert call_args[1]['user_id'] == 1
        assert call_args[1]['token_hash'] == token_hash
        # expires_at should be 7 days in the future (within 1 minute)
        expires_at = call_args[1]['expires_at']
        time_diff = (expires_at - datetime.now(timezone.utc)).total_seconds()
        assert 6.9 * 24 * 3600 < time_diff < 7.1 * 24 * 3600


class TestRefreshAccessToken:
    """Test refreshing access tokens with refresh tokens"""

    def test_refresh_token_with_valid_token(self, auth_service, mock_refresh_token, mock_user):
        """Test successful access token refresh with valid refresh token"""
        # Setup mocks
        auth_service.token_repo.get_refresh_token_by_hash = MagicMock(
            return_value=mock_refresh_token
        )
        auth_service.user_repo.get_user_by_id = MagicMock(return_value=mock_user)
        auth_service.token_repo.rotate_refresh_token = MagicMock()
        auth_service.create_refresh_token = MagicMock(
            return_value=("new_token", "new_hash")
        )
        
        # Execute
        response = auth_service.refresh_access_token("old_token")
        
        # Verify
        assert "access_token" in response
        assert "refresh_token" in response
        assert response["token_type"] == "bearer"
        assert response["user_id"] == 1
        assert response["refresh_token"] == "new_token"
    
    def test_refresh_token_with_invalid_token_hash(self, auth_service):
        """Test refresh fails when token not found in database"""
        auth_service.token_repo.get_refresh_token_by_hash = MagicMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token("invalid_token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in exc_info.value.detail
    
    def test_refresh_token_with_revoked_token(self, auth_service, mock_refresh_token):
        """Test refresh fails when token is revoked"""
        mock_refresh_token.is_valid = MagicMock(return_value=False)
        auth_service.token_repo.get_refresh_token_by_hash = MagicMock(
            return_value=mock_refresh_token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token("revoked_token")
        
        assert exc_info.value.status_code == 401
        assert "invalid or expired" in exc_info.value.detail
    
    def test_refresh_token_with_expired_token(self, auth_service, mock_refresh_token):
        """Test refresh fails when token is expired"""
        mock_refresh_token.is_valid = MagicMock(return_value=False)
        auth_service.token_repo.get_refresh_token_by_hash = MagicMock(
            return_value=mock_refresh_token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token("expired_token")
        
        assert exc_info.value.status_code == 401
    
    def test_refresh_token_when_user_not_found(self, auth_service, mock_refresh_token):
        """Test refresh fails when user doesn't exist"""
        auth_service.token_repo.get_refresh_token_by_hash = MagicMock(
            return_value=mock_refresh_token
        )
        auth_service.user_repo.get_user_by_id = MagicMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token("valid_token")
        
        assert exc_info.value.status_code == 401
    
    def test_refresh_token_performs_rotation(self, auth_service, mock_refresh_token, mock_user):
        """Test that refresh token is rotated (old revoked, new created)"""
        auth_service.token_repo.get_refresh_token_by_hash = MagicMock(
            return_value=mock_refresh_token
        )
        auth_service.user_repo.get_user_by_id = MagicMock(return_value=mock_user)
        auth_service.token_repo.rotate_refresh_token = MagicMock()
        auth_service.create_refresh_token = MagicMock(
            return_value=("new_token", "new_hash")
        )
        
        auth_service.refresh_access_token("old_token")
        
        # Verify rotation was called
        auth_service.token_repo.rotate_refresh_token.assert_called_once()


class TestLoginWithRefreshToken:
    """Test that login returns refresh token"""

    def test_login_returns_refresh_token(self, auth_service, mock_user):
        """Test that login method returns refresh token in response"""
        auth_service.authenticate_user = MagicMock(return_value=mock_user)
        auth_service.create_refresh_token = MagicMock(
            return_value=("refresh_token", "refresh_hash")
        )
        
        response = auth_service.login("test@example.com", "password")
        
        assert "access_token" in response
        assert "refresh_token" in response
        assert response["refresh_token"] == "refresh_token"
        assert response["token_type"] == "bearer"
        assert response["user_id"] == 1
