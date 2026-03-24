from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """Token response schema - includes both access and refresh tokens."""
    access_token: str
    token_type: str
    user_id: int
    refresh_token: Optional[str] = None  # Included on login, not on refresh
    expires_in: int = 3600  # seconds until access token expires


class RefreshTokenResponse(BaseModel):
    """Response schema for token refresh endpoint - always returns both tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int


class TokenRefresh(BaseModel):
    """Request schema for token refresh endpoint."""
    refresh_token: str


class TokenData(BaseModel):
    """JWT payload data."""
    email: str | None = None
