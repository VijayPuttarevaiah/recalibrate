from sqlalchemy.orm import Session
from fastapi import HTTPException
from auth.repositories.user_repository import UserRepository
from auth.register.schemas import UserCreate
from auth.utils.password import hash_password
from sqlalchemy.exc import IntegrityError
from core.logging_config import LogManager

logger = LogManager.get_logger()


class RegisterService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register_user(self, user_data: UserCreate):
        logger.info(f"Registering new user with email: {user_data.email}")
        hashed_pw = hash_password(user_data.password)
        try:
            user = self.user_repo.create_user(user_data, hashed_pw)
            logger.success(f"Successfully registered user: {user.email}")
            return user
        except IntegrityError:
            logger.warning(
                f"Registration failed: Email {user_data.email} already exists"
            )
            raise HTTPException(status_code=400, detail="Email already registered")
