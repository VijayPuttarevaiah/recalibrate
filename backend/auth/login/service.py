from sqlalchemy.orm import Session
from fastapi import HTTPException
from auth.repositories.user_repository import UserRepository
from auth.utils.password import verify_password
from jose import jwt
from datetime import datetime, timedelta, timezone
from config.config import Config
from core.logging_config import LogManager

logger = LogManager.get_logger()

config = Config()
SECRET_KEY = config.config["oauth2"]["secret_key"]
ALGORITHM = config.config["oauth2"].get("algorithm", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    config.config["oauth2"].get("access_token_expire_minutes", "60")
)


class LoginService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def authenticate_user(self, email: str, password: str):
        logger.info(f"Authenticating user: {email}")
        user = self.user_repo.get_user_by_email(email)
        if not user or not verify_password(password, user.password):
            logger.warning(f"Failed authentication attempt for user: {email}")
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        if not user.is_verified:
            logger.warning(f"Authentication failed: User {email} is not verified")
            raise HTTPException(
                status_code=403,
                detail="Email not verified. Please verify your email before logging in.",
            )
        logger.success(f"User authenticated successfully: {email}")
        return user

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        logger.debug(f"Creating access token for: {data.get('sub')}")
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def login_user(self, email: str, password: str) -> dict:
        user = self.authenticate_user(email, password)
        access_token = self.create_access_token(data={"sub": user.email, "id": user.id})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
        }

    def get_current_user_id(self, token: str) -> int:
        """Extract user_id from a valid JWT."""
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id


def login_user(db: Session, email: str, password: str) -> dict:
    """Convenience wrapper for logging in a user using a DB session."""
    service = LoginService(db)
    return service.login_user(email=email, password=password)
