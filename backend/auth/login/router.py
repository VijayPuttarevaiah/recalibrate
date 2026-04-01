from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from auth.login.service import LoginService
from auth.login.schemas import Token
from core.db_session import get_db
from core.logging_config import LogManager

logger = LogManager.get_logger()

# Initialize the router for login-related endpoints
router = APIRouter()

# Endpoint to authenticate a user and provide an access token
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"POST /login request for user: {form_data.username}")
    login_service = LoginService(db)
    result = login_service.login_user(form_data.username, form_data.password)
    logger.info(f"Login successful for user: {form_data.username}")
    return result