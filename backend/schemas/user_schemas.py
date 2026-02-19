import re

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


def _validate_strong_password(password: str) -> str:
    """Enforce strong-password policy (shared across schemas)."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must include at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must include at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must include at least one digit.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must include at least one special character.")
    return password


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return _validate_strong_password(v)

class UserResponse(UserBase):
    id: int
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)

class RegisterRequest(UserCreate):
    pass
