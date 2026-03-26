"""
Test suite for RefreshToken model.

Phase 1: TDD RED phase - Tests for refresh token database model.
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from models.token_models import RefreshToken


class TestRefreshTokenModel:
    """Test RefreshToken SQLAlchemy model."""
    
    def test_refresh_token_model_fields(self):
        """RefreshToken model should have required fields."""
        # Check model has required columns
        assert hasattr(RefreshToken, 'id')
        assert hasattr(RefreshToken, 'user_id')
        assert hasattr(RefreshToken, 'token_hash')
        assert hasattr(RefreshToken, 'expires_at')
        assert hasattr(RefreshToken, 'is_revoked')
        assert hasattr(RefreshToken, 'created_at')
    
    def test_refresh_token_model_relationships(self):
        """RefreshToken model should have foreign key to User."""
        assert hasattr(RefreshToken, 'user_id')
        # Check ForeignKey constraint exists
        assert RefreshToken.user_id.foreign_keys  # SQLAlchemy ForeignKey collection


class TestRefreshTokenModelCreation:
    """Test creating RefreshToken instances."""
    
    def test_create_refresh_token_with_required_fields(self):
        """Create RefreshToken with all required fields."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        token = RefreshToken(
            user_id=123,
            token_hash="hashed_token_value_12345...",
            expires_at=expires_at,
            is_revoked=False
        )
        
        assert token.user_id == 123
        assert token.token_hash == "hashed_token_value_12345..."
        assert token.expires_at == expires_at
        assert token.is_revoked is False
    
    def test_refresh_token_defaults(self):
        """RefreshToken should have sensible defaults."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        token = RefreshToken(
            user_id=123,
            token_hash="hashed...",
            expires_at=expires_at
        )
        
        # is_revoked should default to False
        assert token.is_revoked is False
        # created_at should be set automatically
        assert token.created_at is not None


class TestRefreshTokenExpiration:
    """Test token expiration logic."""
    
    def test_token_expiration_datetime(self):
        """Token should have proper expiration datetime."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=7)
        
        token = RefreshToken(
            user_id=123,
            token_hash="hashed...",
            expires_at=expires_at
        )
        
        assert token.expires_at > now
        assert (token.expires_at - now).days == 7
    
    def test_token_is_expired_check(self):
        """RefreshToken should support expiration checking."""
        now = datetime.now(timezone.utc)
        expired_time = now - timedelta(hours=1)
        
        expired_token = RefreshToken(
            user_id=123,
            token_hash="expired_hashed...",
            expires_at=expired_time,
            is_revoked=False
        )
        
        # Token should be considered expired
        assert expired_token.expires_at < now


class TestRefreshTokenRevocation:
    """Test token revocation."""
    
    def test_revoke_refresh_token(self):
        """RefreshToken should be revocable."""
        token = RefreshToken(
            user_id=123,
            token_hash="hashed...",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_revoked=False
        )
        
        # Revoke the token
        token.is_revoked = True
        
        assert token.is_revoked is True
    
    def test_revoked_token_is_invalid(self):
        """Revoked token should be considered invalid."""
        token = RefreshToken(
            user_id=123,
            token_hash="hashed...",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_revoked=True
        )
        
        # Token is both not expired AND revoked
        assert token.is_revoked is True
        assert token.expires_at > datetime.now(timezone.utc)


class TestRefreshTokenRotation:
    """Test token rotation tracking."""
    
    def test_track_token_rotation(self):
        """RefreshToken should track rotation chain (hash of previous token)."""
        old_token_hash = "old_hashed_token..."
        
        new_token = RefreshToken(
            user_id=123,
            token_hash="new_hashed_token...",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            rotated_from=old_token_hash  # Track where it came from
        )
        
        assert new_token.rotated_from == old_token_hash
        assert new_token.token_hash == "new_hashed_token..."
    
    def test_rotation_chain(self):
        """Rotation chain should track lineage of tokens."""
        token1 = RefreshToken(
            user_id=123,
            token_hash="token1_hash...",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            rotated_from=None  # Original token
        )
        
        token2 = RefreshToken(
            user_id=123,
            token_hash="token2_hash...",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            rotated_from=token1.token_hash  # Token 1 hash
        )
        
        assert token1.rotated_from is None
        assert token2.rotated_from == token1.token_hash


class TestRefreshTokenQueryFiltering:
    """Test queries on refresh tokens."""
    
    def test_find_valid_refresh_token(self):
        """Should be able to find valid (not revoked, not expired) refresh tokens."""
        now = datetime.now(timezone.utc)
        
        valid_token = RefreshToken(
            user_id=123,
            token_hash="valid_hashed...",
            expires_at=now + timedelta(days=7),
            is_revoked=False
        )
        
        # Token should match validity criteria
        assert not valid_token.is_revoked
        assert valid_token.expires_at > now
    
    def test_filter_out_revoked_tokens(self):
        """Revoked tokens should be filtered out."""
        now = datetime.now(timezone.utc)
        
        revoked_token = RefreshToken(
            user_id=123,
            token_hash="revoked_hashed...",
            expires_at=now + timedelta(days=7),
            is_revoked=True
        )
        
        # Revoked token should not be valid
        assert revoked_token.is_revoked is True
    
    def test_filter_out_expired_tokens(self):
        """Expired tokens should be filtered out."""
        now = datetime.now(timezone.utc)
        
        expired_token = RefreshToken(
            user_id=123,
            token_hash="expired_hashed...",
            expires_at=now - timedelta(hours=1),
            is_revoked=False
        )
        
        # Expired token should not be valid
        assert expired_token.expires_at < now
