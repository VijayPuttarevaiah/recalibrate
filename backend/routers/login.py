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
    """Authenticate user and return access token.
    
    Refactored: Router is now a thin wrapper that delegates to auth_service.login().
    This fixes the Feature Envy issue where the router was orchestrating multiple
    service calls and building the response manually.
    
    Args:
        form_data: OAuth2 form with username and password
        db: Database session
        
    Returns:
        Token response with access_token, token_type, and user_id
    """
    logger.info(f"POST /login request for user: {form_data.username}")
    auth_service = AuthService(db)
    return auth_service.login(form_data.username, form_data.password)