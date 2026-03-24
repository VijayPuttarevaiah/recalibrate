from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import expression
from models.base import Base

# Model to store tokens that have been invalidated (logged out) before their expiration
class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # The actual JWT token string
    token = Column(String(512), unique=True, nullable=False)
    # Timestamp when the token was blacklisted
    blacklisted_on = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class RefreshToken(Base):
    """Refresh token model for long-lived authentication."""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    token_hash = Column(String(512), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_revoked = Column(Boolean, nullable=False, default=False, server_default=expression.false())
    rotated_from = Column(String(512), nullable=True)
    
    def __init__(self, user_id: int, token_hash: str, expires_at, 
                 is_revoked: bool = False, rotated_from: str = None, **kwargs):
        """Initialize RefreshToken with defaults."""
        super().__init__(**kwargs)
        self.user_id = user_id
        self.token_hash = token_hash
        self.expires_at = expires_at
        self.is_revoked = is_revoked
        self.rotated_from = rotated_from
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
    
    def is_valid(self) -> bool:
        """Check if token is valid (not revoked and not expired)."""
        now = datetime.now(timezone.utc)
        return not self.is_revoked and self.expires_at > now
    
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return self.expires_at < datetime.now(timezone.utc)