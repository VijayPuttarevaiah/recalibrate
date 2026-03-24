from sqlalchemy.orm import Session
from models.token_models import BlacklistedToken, RefreshToken
from datetime import datetime, timezone
from utils.logging_config import LogManager

logger = LogManager.get_logger()

class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def is_token_blacklisted(self, token: str) -> bool:
        logger.debug("Checking if token is blacklisted")
        return self.db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first() is not None

    def blacklist_token(self, token: str):
        logger.debug("Adding token to blacklist in DB")
        new_blacklisted_token = BlacklistedToken(
            token=token, 
            blacklisted_on=datetime.now(timezone.utc)
        )
        self.db.add(new_blacklisted_token)
        self.db.commit()
        logger.debug("Token successfully blacklisted in DB")
        return new_blacklisted_token

    def create_refresh_token(self, user_id: int, token_hash: str, expires_at) -> RefreshToken:
        """Create and store a new refresh token for a user"""
        logger.debug(f"Creating refresh token for user {user_id}")
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False
        )
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        logger.debug(f"Refresh token created successfully for user {user_id}")
        return refresh_token

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken:
        """Retrieve a refresh token by its hash"""
        logger.debug("Retrieving refresh token by hash")
        token = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        return token

    def rotate_refresh_token(self, old_token_hash: str, new_token_hash: str, expires_at) -> RefreshToken:
        """Rotate a refresh token: revoke old, create new with rotation chain"""
        logger.debug("Rotating refresh token")
        
        # Get the old token to revoke
        old_token = self.get_refresh_token_by_hash(old_token_hash)
        if not old_token:
            logger.warning(f"Old token not found: {old_token_hash}")
            return None
        
        # Revoke the old token
        old_token.is_revoked = True
        self.db.add(old_token)
        self.db.commit()
        
        # Create new token with rotation chain
        new_token = RefreshToken(
            user_id=old_token.user_id,
            token_hash=new_token_hash,
            expires_at=expires_at,
            is_revoked=False,
            rotated_from=old_token_hash
        )
        self.db.add(new_token)
        self.db.commit()
        self.db.refresh(new_token)
        
        logger.debug(f"Refresh token rotated successfully for user {old_token.user_id}")
        return new_token

    def revoke_all_user_tokens(self, user_id: int):
        """Revoke all refresh tokens for a user"""
        logger.debug(f"Revoking all refresh tokens for user {user_id}")
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        self.db.commit()
        logger.debug(f"All refresh tokens revoked for user {user_id}")
