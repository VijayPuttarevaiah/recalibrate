from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from .base import Base

# Model to store tokens that have been invalidated (logged out) before their expiration
class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # The actual JWT token string
    token = Column(String(512), unique=True, nullable=False)
    # Timestamp when the token was blacklisted
    blacklisted_on = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
