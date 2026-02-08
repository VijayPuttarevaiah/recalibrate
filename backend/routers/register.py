# Import necessary modules from FastAPI, SQLAlchemy, and utilities
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from schemas.user_schemas import RegisterRequest
from services.auth_service import AuthService
from utils.db_session import get_db
from utils.logging_config import LogManager

logger = LogManager.get_logger()

# Initialize the router for registration-related endpoints
router = APIRouter()

# Endpoint to register a new user
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    logger.info(f"POST /register request for email: {user.email}")
    auth_service = AuthService(db)
    auth_service.register_user(user)
    return {"msg": "User registered successfully"}