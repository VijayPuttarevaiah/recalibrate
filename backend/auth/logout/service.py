from sqlalchemy.orm import Session
from auth.repositories.token_repository import TokenRepository
from core.logging_config import LogManager

logger = LogManager.get_logger()


class LogoutService:
    def __init__(self, db: Session):
        self.db = db

    def logout_user(self, token: str, db: Session):
        logger.info("Blacklisting token for logout")
        token_repo = TokenRepository(db)
        return token_repo.logout_token(token)
