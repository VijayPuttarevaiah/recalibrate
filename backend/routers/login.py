from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from services.auth_service import AuthService
from utils.db_session import get_db
from schemas.token_schemas import Token
from utils.logging_config import LogManager

logger = LogManager.get_logger()

# Initialize the router for login-related endpoints
router = APIRouter()

# Endpoint to authenticate a user and provide an access token
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"POST /login request for user: {form_data.username}")
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    
    # Generate and return the access token
    access_token = auth_service.create_access_token(data={"sub": user.email})
    logger.info(f"Login successful for user: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}