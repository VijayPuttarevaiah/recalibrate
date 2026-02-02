# Import necessary modules from FastAPI, SQLAlchemy, and utilities
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from models.user_models import User
from models.base import Base
from utils.password import hash_password
from sqlalchemy.exc import IntegrityError
from utils.db_session import DBSession
from datetime import timezone,datetime


# Initialize database session
SessionLocal = DBSession().SessionLocal

# Initialize the router for registration-related endpoints
router = APIRouter()

# Schema for registration request validation
class RegisterRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str

# Dependency to get a local database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint to register a new user
@router.post("/register")
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    # Hash the user's password for secure storage
    hashed_pw = hash_password(user.password)
    # Create a new User object from the request data
    db_user = User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        password=hashed_pw,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    # Add the user to the database session
    db.add(db_user)
    try:
        # Commit the transaction to the database
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        # Roll back the transaction if there is a conflict (e.g., duplicate email)
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    # Return a success message
    
    return {"msg": "User registered successfully"}