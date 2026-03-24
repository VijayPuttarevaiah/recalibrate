from sqlalchemy.orm import Session
from models.user_models import User
from schemas.user_schemas import UserCreate
from datetime import datetime, timezone
from utils.logging_config import LogManager

logger = LogManager.get_logger()

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        logger.debug(f"Fetching user by email: {email}")
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> User | None:
        logger.debug(f"Fetching user by id: {user_id}")
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        logger.debug(f"Creating user record in DB for: {user_data.email}")
        db_user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=hashed_password,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        logger.debug(f"User record created: {db_user.email}")
        return db_user

    def update_user_verification(self, email: str, is_verified: bool):
        logger.debug(f"Updating verification status for {email} to {is_verified}")
        user = self.get_user_by_email(email)
        if user:
            user.is_verified = is_verified
            self.db.commit()
            self.db.refresh(user)
            logger.debug(f"Verification status updated for {email}")
        return user

    def update_password(self, email: str, hashed_password: str):
        logger.debug(f"Updating password for user: {email}")
        user = self.get_user_by_email(email)
        if user:
            user.password = hashed_password
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(user)
            logger.debug(f"Password updated successfully for {email}")
        return user
