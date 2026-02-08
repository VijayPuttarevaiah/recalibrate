from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)

class RegisterRequest(UserCreate):
    pass
