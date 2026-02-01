from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from models.user_models import User
from models.base import Base
from utils.password import hash_password
from sqlalchemy.exc import IntegrityError
from utils.db_session import DBSession
from datetime import timezone,datetime


SessionLocal = DBSession().SessionLocal

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    hashed_pw = hash_password(user.password)
    db_user = User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        password=hashed_pw,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    return {"msg": "User registered successfully"}