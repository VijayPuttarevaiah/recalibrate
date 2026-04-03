import time
from fastapi import HTTPException
from sqlalchemy.orm import Session
from auth.repositories.user_repository import UserRepository
from auth.utils.email_sender import send_email
from auth.utils.password import hash_password
from core.logging_config import LogManager
import random
import string

logger = LogManager.get_logger()

# In-memory storage for reset codes (similar to verification codes)
# In production, this should be in Redis or DB
reset_codes = {}
RESET_CODE_EXPIRY_SECONDS = 60  # 1 minute

DEFAULT_CODE_LENGTH = 8


class PasswordResetService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def generate_code(self, length=DEFAULT_CODE_LENGTH):
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def initiate_password_reset(self, email: str):
        logger.info(f"Initiating password reset for: {email}")
        user = self.user_repo.get_user_by_email(email)
        if not user:
            # We don't want to leak if an email exists, but for this project's scope
            # and consistency with other routes, we'll keep it simple.
            logger.warning(f"Password reset requested for non-existent email: {email}")
            raise HTTPException(status_code=404, detail="User not found")

        code = self.generate_code()
        expiry = time.time() + RESET_CODE_EXPIRY_SECONDS
        reset_codes[email] = (code, expiry)

        subject = "Password Reset Request"
        body = (
            f"Your password reset code is: {code}\nThis code will expire in 10 minutes."
        )

        try:
            send_email(email, subject, body)
            logger.success(f"Reset code sent to: {email}")
        except Exception as e:
            logger.error(f"Failed to send reset email to {email}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send reset email")

        return {"msg": "Password reset code sent to email"}

    def verify_password_reset_code(self, email: str, code: str):
        logger.info(f"Verifying password reset code for: {email}")
        entry = reset_codes.get(email)

        if not entry:
            logger.warning(f"Verification failed: No code found for {email}")
            raise HTTPException(
                status_code=400, detail="No reset request found for this email"
            )

        stored_code, expiry = entry
        if time.time() > expiry:
            logger.warning(f"Verification failed: Code expired for {email}")
            del reset_codes[email]
            raise HTTPException(status_code=400, detail="Reset code expired")

        if code.upper() != stored_code:
            logger.warning(f"Verification failed: Invalid code for {email}")
            raise HTTPException(status_code=400, detail="Invalid reset code")

        return {"msg": "Code verified"}

    def confirm_password_reset(self, email: str, code: str, new_password: str):
        logger.info(f"Confirming password reset for: {email}")
        entry = reset_codes.get(email)

        if not entry:
            logger.warning(f"Reset failed: No code found for {email}")
            raise HTTPException(
                status_code=400, detail="No reset request found for this email"
            )

        stored_code, expiry = entry
        if time.time() > expiry:
            logger.warning(f"Reset failed: Code expired for {email}")
            del reset_codes[email]
            raise HTTPException(status_code=400, detail="Reset code expired")

        if code.upper() != stored_code:
            logger.warning(f"Reset failed: Invalid code for {email}")
            raise HTTPException(status_code=400, detail="Invalid reset code")

        hashed_pw = hash_password(new_password)
        user = self.user_repo.update_password(email, hashed_pw)

        if not user:
            logger.error(f"Reset failed: User {email} not found during update")
            raise HTTPException(status_code=404, detail="User not found")

        # Clear the reset code after successful reset
        del reset_codes[email]
        logger.success(f"Password reset successful for: {email}")

        return {"msg": "Password has been reset successfully"}
