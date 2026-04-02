import random
import string
import time
from fastapi import HTTPException
from sqlalchemy.orm import Session
from auth.repositories.user_repository import UserRepository
from auth.utils.email_sender import send_email
from core.logging_config import LogManager

logger = LogManager.get_logger()

verification_codes = {}
CODE_EXPIRY_SECONDS = 70
DEFAULT_CODE_LENGTH = 6


class VerificationService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def generate_code(self, length=DEFAULT_CODE_LENGTH):
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def send_verification_code(self, email: str):
        logger.info(f"Generating verification code for: {email}")
        code = self.generate_code()
        expiry = time.time() + CODE_EXPIRY_SECONDS
        verification_codes[email] = (code, expiry)

        subject = "Your Verification Code"
        body = f"Your verification code is: {code}"
        try:
            send_email(email, subject, body)
            logger.success(f"Verification code sent successfully to: {email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to send email: {str(e)}"
            )
        return {"msg": "Verification code sent to email"}

    def verify_email(self, email: str, code: str):
        logger.info(f"Verifying email: {email} with code: {code}")
        entry = verification_codes.get(email)
        if not entry:
            logger.warning(f"Verification failed: No code found for {email}")
            raise HTTPException(status_code=404, detail="No code sent to this email")

        stored_code, expiry = entry
        if time.time() > expiry:
            logger.warning(f"Verification failed: Code expired for {email}")
            del verification_codes[email]
            raise HTTPException(status_code=400, detail="Verification code expired")

        if code.upper() != stored_code:
            logger.warning(f"Verification failed: Invalid code for {email}")
            raise HTTPException(status_code=400, detail="Invalid verification code")

        user = self.user_repo.update_user_verification(email, True)
        if not user:
            logger.error(f"Verification failed: User {email} not found in database")
            raise HTTPException(status_code=404, detail="User not found")

        del verification_codes[email]
        logger.success(f"Email verified successfully: {email}")
        return {"msg": "Email verified successfully"}
