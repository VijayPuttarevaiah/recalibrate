from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from auth.password_reset.service import PasswordResetService
from auth.password_reset.schemas import ForgotPasswordRequest, ResetPasswordConfirm, VerifyResetCodeRequest
from core.db_session import get_db
from core.logging_config import LogManager

logger = LogManager.get_logger()

router = APIRouter()


def _service(db: Session) -> PasswordResetService:
    return PasswordResetService(db)

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    logger.info(f"POST /forgot-password for: {request.email}")
    return _service(db).initiate_password_reset(request.email)

@router.post("/verify-reset-code", status_code=status.HTTP_200_OK)
def verify_reset_code(request: VerifyResetCodeRequest, db: Session = Depends(get_db)):
    logger.info(f"POST /verify-reset-code for: {request.email}")
    return _service(db).verify_password_reset_code(request.email, request.code)

@router.post("/resend-reset-code", status_code=status.HTTP_200_OK)
def resend_reset_code(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    logger.info(f"POST /resend-reset-code for: {request.email}")
    return _service(db).initiate_password_reset(request.email)

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(request: ResetPasswordConfirm, db: Session = Depends(get_db)):
    logger.info(f"POST /reset-password for: {request.email}")
    return _service(db).confirm_password_reset(request.email, request.code, request.new_password)
