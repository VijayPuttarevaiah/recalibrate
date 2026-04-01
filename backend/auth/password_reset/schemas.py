from pydantic import BaseModel, EmailStr, Field, field_validator

from auth.register.schemas import validate_strong_password


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str

class ResetPasswordConfirm(BaseModel):
    email: EmailStr
    code: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_strong_password(v)
