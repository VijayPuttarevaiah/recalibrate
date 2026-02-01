from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.user_models import User
from utils.password import verify_password
from jose import jwt
from datetime import datetime, timedelta,timezone
from utils.db_session import DBSession
from config.config import Config

SessionLocal = DBSession().SessionLocal
config = Config()
SECRET_KEY = config.config['oauth2']['secret_key']
ALGORITHM = config.config['oauth2'].get('algorithm', "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.config['oauth2'].get('access_token_expire_minutes', "30"))

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified. Please verify your email before logging in.")
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}