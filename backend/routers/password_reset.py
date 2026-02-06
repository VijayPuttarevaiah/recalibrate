from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from utils.db_session import get_db
from services.password_reset_service import PasswordResetService
from schemas.password_reset_schemas import ForgotPasswordRequest, ResetPasswordConfirm
from utils.logging_config import LogManager

logger = LogManager.get_logger()
router = APIRouter()

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    logger.info(f"POST /forgot-password for: {request.email}")
    service = PasswordResetService(db)
    return service.initiate_password_reset(request.email)

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(request: ResetPasswordConfirm, db: Session = Depends(get_db)):
    logger.info(f"POST /reset-password for: {request.email}")
    service = PasswordResetService(db)
    return service.confirm_password_reset(request.email, request.code, request.new_password)
