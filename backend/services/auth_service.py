from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from repositories.user_repository import UserRepository
from schemas.user_schemas import UserCreate
from utils.password import hash_password, verify_password
from jose import jwt
from datetime import datetime, timedelta, timezone
from config.config import Config
from sqlalchemy.exc import IntegrityError
from utils.logging_config import LogManager

logger = LogManager.get_logger()

config = Config()
SECRET_KEY = config.config['oauth2']['secret_key']
ALGORITHM = config.config['oauth2'].get('algorithm', "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.config['oauth2'].get('access_token_expire_minutes', "30"))

class AuthService:
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
            logger.warning(f"Registration failed: Email {user_data.email} already exists")
            raise HTTPException(status_code=400, detail="Email already registered")

    def authenticate_user(self, email: str, password: str):
        logger.info(f"Authenticating user: {email}")
        user = self.user_repo.get_user_by_email(email)
        if not user or not verify_password(password, user.password):
            logger.warning(f"Failed authentication attempt for user: {email}")
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        if not user.is_verified:
            logger.warning(f"Authentication failed: User {email} is not verified")
            raise HTTPException(status_code=403, detail="Email not verified. Please verify your email before logging in.")
        logger.success(f"User authenticated successfully: {email}")
        return user

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        logger.debug(f"Creating access token for: {data.get('sub')}")
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def logout_user(self, token: str, db: Session):
        logger.info("Blacklisting token for logout")
        from repositories.token_repository import TokenRepository
        token_repo = TokenRepository(db)
        if token_repo.is_token_blacklisted(token):
            logger.debug("Token was already blacklisted")
            return {"msg": "Token already blacklisted"}
        token_repo.blacklist_token(token)
        logger.success("Token blacklisted successfully")
        return {"msg": "Successfully logged out"}
    
    def get_current_user_id(self, token: str) -> int:
        """Extract user_id from a valid JWT."""
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id