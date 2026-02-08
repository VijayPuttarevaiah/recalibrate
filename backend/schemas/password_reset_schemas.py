from pydantic import BaseModel, EmailStr, Field

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str

class ResetPasswordConfirm(BaseModel):
    email: EmailStr
    code: str
    new_password: str = Field(..., min_length=8)
