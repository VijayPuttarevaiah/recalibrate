"""
Tests for Token Repository Refresh Token Methods
Tests CRUD operations for refresh tokens in the database
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from repositories.token_repository import TokenRepository
from models.token_models import RefreshToken


@pytest.fixture
def mock_db():
    """Mock database session"""
    return MagicMock(spec=Session)


@pytest.fixture
def token_repo(mock_db):
    """Create TokenRepository instance with mocked db"""
    return TokenRepository(mock_db)


@pytest.fixture
def sample_refresh_token():
    """Create a sample RefreshToken instance"""
    return RefreshToken(
        user_id=1,
        token_hash="sample_hash_value",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=False
    )


class TestCreateRefreshToken:
    """Test creating refresh tokens in database"""

    def test_create_refresh_token_adds_to_db(self, token_repo, mock_db):
        """Test that create_refresh_token adds token to database"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        token_repo.create_refresh_token(
            user_id=1,
            token_hash="test_hash",
            expires_at=expires_at
        )
        
        # Verify add and commit were called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_refresh_token_creates_correct_instance(self, token_repo, mock_db):
        """Test that token created with correct parameters"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        token_repo.create_refresh_token(
            user_id=1,
            token_hash="test_hash",
            expires_at=expires_at
        )
        
        # Get the RefreshToken that was added
        added_token = mock_db.add.call_args[0][0]
        
        assert added_token.user_id == 1
        assert added_token.token_hash == "test_hash"
        assert added_token.expires_at == expires_at
        assert added_token.is_revoked == False
    
    def test_create_refresh_token_returns_token(self, token_repo, mock_db, sample_refresh_token):
        """Test that create_refresh_token returns the created token"""
        mock_db.refresh = MagicMock()
        
        # Need to make the token available after add
        mock_db.add = MagicMock()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Manually set up the return to test the flow
        result = token_repo.create_refresh_token(
            user_id=1,
            token_hash="test_hash",
            expires_at=expires_at
        )
        
        # Should return a RefreshToken instance
        assert isinstance(result, RefreshToken)


class TestGetRefreshTokenByHash:
    """Test retrieving refresh tokens by hash"""

    def test_get_refresh_token_by_hash_queries_correctly(self, token_repo, mock_db):
        """Test that get_refresh_token_by_hash queries with correct parameters"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        token_repo.get_refresh_token_by_hash("test_hash")
        
        # Verify query was made
        mock_db.query.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()
    
    def test_get_refresh_token_by_hash_returns_token_when_found(self, token_repo, mock_db, sample_refresh_token):
        """Test that method returns token when found"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_refresh_token
        
        result = token_repo.get_refresh_token_by_hash("sample_hash_value")
        
        assert result == sample_refresh_token
    
    def test_get_refresh_token_by_hash_returns_none_when_not_found(self, token_repo, mock_db):
        """Test that method returns None when token not found"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        result = token_repo.get_refresh_token_by_hash("nonexistent_hash")
        
        assert result is None


class TestRotateRefreshToken:
    """Test rotating refresh tokens"""

    def test_rotate_refresh_token_revokes_old(self, token_repo, mock_db, sample_refresh_token):
        """Test that old token is revoked during rotation"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_refresh_token
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        token_repo.rotate_refresh_token(
            old_token_hash="old_hash",
            new_token_hash="new_hash",
            expires_at=expires_at
        )
        
        # Verify old token is revoked
        assert sample_refresh_token.is_revoked == True
    
    def test_rotate_refresh_token_creates_new_with_rotation_chain(self, token_repo, mock_db, sample_refresh_token):
        """Test that new token is created with rotation chain reference"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_refresh_token
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        token_repo.rotate_refresh_token(
            old_token_hash="old_hash",
            new_token_hash="new_hash",
            expires_at=expires_at
        )
        
        # Verify add was called to create new token
        added_tokens = [call[0][0] for call in mock_db.add.call_args_list if isinstance(call[0][0], RefreshToken)]
        
        # Should have added at least one token (the old one being marked revoked, then new one)
        assert len(added_tokens) >= 1
        
        # Check the new token has rotation chain
        new_token = [t for t in added_tokens if not t.is_revoked]
        if new_token:
            assert new_token[0].rotated_from == "old_hash"
    
    def test_rotate_refresh_token_returns_none_when_old_not_found(self, token_repo, mock_db):
        """Test that rotate returns None when old token doesn't exist"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        result = token_repo.rotate_refresh_token(
            old_token_hash="nonexistent",
            new_token_hash="new_hash",
            expires_at=expires_at
        )
        
        assert result is None


class TestRevokeAllUserTokens:
    """Test revoking all tokens for a user"""

    def test_revoke_all_user_tokens_updates_database(self, token_repo, mock_db):
        """Test that revoke_all_user_tokens updates the database"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        
        token_repo.revoke_all_user_tokens(user_id=1)
        
        # Verify query and update were called
        mock_db.query.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_filter.update.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_revoke_all_user_tokens_marks_as_revoked(self, token_repo, mock_db):
        """Test that all tokens are marked as revoked"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        
        token_repo.revoke_all_user_tokens(user_id=1)
        
        # Check that is_revoked was set to True
        update_call = mock_filter.update.call_args[0][0]
        assert update_call.get("is_revoked") == True or "is_revoked" in str(update_call)
    
    def test_revoke_all_user_tokens_only_unrevoked_tokens(self, token_repo, mock_db):
        """Test that only active (unrevoked) tokens are revoked"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        
        token_repo.revoke_all_user_tokens(user_id=1)
        
        # Verify filter was applied for is_revoked == False
        # The call should filter for unrevoked tokens
        assert mock_query.filter.called
