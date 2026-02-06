from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.user_models import User
from utils.password import verify_password
from jose import jwt
from datetime import datetime, timedelta, timezone
from utils.db_session import DBSession
from config.config import Config

# Initialize database session and configuration
SessionLocal = DBSession().SessionLocal
config = Config()
# Extract OAuth2 settings from configuration
SECRET_KEY = config.config['oauth2']['secret_key']
ALGORITHM = config.config['oauth2'].get('algorithm', "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.config['oauth2'].get('access_token_expire_minutes', "30"))

# Initialize the router for login-related endpoints
router = APIRouter()

# Dependency to get a local database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to generate a JWT access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    # Set the expiration time for the token
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    # Encode the token using the secret key and specified algorithm
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Endpoint to authenticate a user and provide an access token
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Find the user by their email address
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Check if user exists and the provided password is correct
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    # Ensure the user's email has been verified before allowing login
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified. Please verify your email before logging in.")
    # Generate and return the access token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}