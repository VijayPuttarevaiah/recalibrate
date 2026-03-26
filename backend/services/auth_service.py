from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from repositories.user_repository import UserRepository
from repositories.token_repository import TokenRepository
from schemas.user_schemas import UserCreate
from utils.password import hash_password, verify_password
from jose import jwt
from datetime import datetime, timedelta, timezone
from config.config import Config
from sqlalchemy.exc import IntegrityError
from utils.logging_config import LogManager
from typing import Dict, Any
import hashlib
import secrets

logger = LogManager.get_logger()

config = Config()
SECRET_KEY = config.config['oauth2']['secret_key']
ALGORITHM = config.config['oauth2'].get('algorithm', "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.config['oauth2'].get('access_token_expire_minutes', "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(config.config['oauth2'].get('refresh_token_expire_days', "7"))

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = TokenRepository(db)

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

    def _hash_token(self, token: str) -> str:
        """Hash a refresh token before storing in database"""
        return hashlib.sha256(token.encode()).hexdigest()

    def _generate_refresh_token(self) -> str:
        """Generate a secure random refresh token string"""
        return secrets.token_urlsafe(64)

    def create_refresh_token(self, user_id: int) -> tuple[str, str]:
        """Create a refresh token and store it in the database.
        
        Args:
            user_id: The user for whom to create the token
            
        Returns:
            Tuple of (token_string, token_hash) where token_string is sent to client
            and token_hash is stored in database
        """
        logger.debug(f"Creating refresh token for user {user_id}")
        
        # Generate token and hash
        token = self._generate_refresh_token()
        token_hash = self._hash_token(token)
        
        # Calculate expiration (7 days from now)
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Store in database
        self.token_repo.create_refresh_token(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        
        logger.debug(f"Refresh token created for user {user_id}")
        return token, token_hash

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Use a refresh token to get a new access token.
        
        Args:
            refresh_token: The refresh token string provided by client
            
        Returns:
            Dict with new access_token, refresh_token, token_type, and user_id
            
        Raises:
            HTTPException: If refresh token is invalid, expired, or revoked
        """
        logger.debug("Attempting to refresh access token")
        
        # Hash the provided token to look it up in database
        token_hash = self._hash_token(refresh_token)
        
        # Retrieve from database
        db_token = self.token_repo.get_refresh_token_by_hash(token_hash)
        if not db_token:
            logger.warning("Refresh token not found")
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Validate token (not revoked and not expired)
        if not db_token.is_valid():
            logger.warning(f"Invalid refresh token for user {db_token.user_id}")
            raise HTTPException(status_code=401, detail="Refresh token is invalid or expired")
        
        # Get user
        user = self.user_repo.get_user_by_id(db_token.user_id)
        if not user:
            logger.error(f"User {db_token.user_id} not found for valid refresh token")
            raise HTTPException(status_code=401, detail="User not found")
        
        # Rotate the token: new token created, old one revoked
        new_token, new_token_hash = self.create_refresh_token(user.id)
        self.token_repo.rotate_refresh_token(
            old_token_hash=token_hash,
            new_token_hash=new_token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        # Generate new access token
        new_access_token = self.create_access_token(
            data={"sub": user.email, "id": user.id}
        )
        
        logger.info(f"Access token refreshed for user {user.id}")
        return {
            "access_token": new_access_token,
            "refresh_token": new_token,
            "token_type": "bearer",
            "user_id": user.id
        }

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Complete login workflow - authenticate user and return token.
        
        This method encapsulates the authentication logic that was previously
        scattered in the router, fixing the Feature Envy architectural issue.
        
        Args:
            username: User email (for OAuth2PasswordRequestForm compatibility)
            password: User password
            
        Returns:
            Dict with access_token, refresh_token, token_type, and user_id
            
        Raises:
            HTTPException: If authentication fails or email not verified
        """
        # Authenticate user (email validation, password verification, email verification check)
        user = self.authenticate_user(username, password)
        
        # Generate access token with user info
        access_token = self.create_access_token(
            data={"sub": user.email, "id": user.id}
        )
        
        # Generate refresh token
        refresh_token, _ = self.create_refresh_token(user.id)
        
        # Return standardized token response with both tokens
        logger.info(f"Login successful for user: {user.email}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user.id
        }

    def logout_user(self, token: str):
        logger.info("Blacklisting token for logout")
        if self.token_repo.is_token_blacklisted(token):
            logger.debug("Token was already blacklisted")
            return {"msg": "Token already blacklisted"}
        self.token_repo.blacklist_token(token)
        logger.success("Token blacklisted successfully")
        return {"msg": "Successfully logged out"}
    
    def get_current_user_id(self, token: str) -> int:
        """Extract user_id from a valid JWT."""
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id