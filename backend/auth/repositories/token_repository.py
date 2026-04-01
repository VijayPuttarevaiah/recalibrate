from sqlalchemy.orm import Session
from auth.models.token_models import BlacklistedToken
from datetime import datetime, timezone
from core.logging_config import LogManager

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

    def logout_token(self, token: str) -> dict:
        if self.is_token_blacklisted(token):
            logger.debug("Token was already blacklisted")
            return {"msg": "Token already blacklisted"}
        self.blacklist_token(token)
        logger.success("Token blacklisted successfully")
        return {"msg": "Successfully logged out"}
