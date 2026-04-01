import re

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


MIN_PASSWORD_LENGTH = 1

def validate_strong_password(password: str) -> str:
    """Minimal password validation shared across schemas."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    return password


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_strong_password(v)

class UserResponse(UserBase):
    id: int
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)

class RegisterRequest(UserCreate):
    pass
