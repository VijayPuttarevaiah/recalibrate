# Import necessary modules from FastAPI, SQLAlchemy, and services
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth.email_verification.service import VerificationService
from auth.email_verification.schemas import SendCodeRequest, VerifyCodeRequest
from core.db_session import get_db
from core.logging_config import LogManager

logger = LogManager.get_logger()

# Initialize the router for email verification endpoints
router = APIRouter()

# Endpoint to generate and send a verification code to a user's email
@router.post("/send-code")
def send_code(request: SendCodeRequest, db: Session = Depends(get_db)):
    logger.info(f"POST /send-code request for: {request.email}")
    verification_service = VerificationService(db)
    return verification_service.send_verification_code(request.email)

# Endpoint to verify the user's email using the code provided
@router.post("/verify")
def verify_email(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    logger.info(f"POST /verify request for: {request.email}")
    verification_service = VerificationService(db)
    return verification_service.verify_email(request.email, request.code)