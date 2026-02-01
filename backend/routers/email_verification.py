from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import random, string, time
from utils.email_sender import send_email
from sqlalchemy.orm import Session
from models.user_models import User
from utils.db_session import DBSession

router = APIRouter()

# In-memory store: {email: (code, expiry_time)}
verification_codes = {}
CODE_EXPIRY_SECONDS = 10 * 60  # 10 minutes

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class SendCodeRequest(BaseModel):
    email: EmailStr

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

def get_db():
    db = DBSession().SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/send-code")
def send_code(request: SendCodeRequest):
    code = generate_code()
    expiry = time.time() + CODE_EXPIRY_SECONDS
    verification_codes[request.email] = (code, expiry)
    # Send email using utility
    subject = "Your Verification Code"
    body = f"Your verification code is: {code}"
    try:
        send_email(request.email, subject, body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    return {"msg": "Verification code sent to email"}

@router.post("/verify")
def verify_email(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    entry = verification_codes.get(request.email)
    if not entry:
        raise HTTPException(status_code=404, detail="No code sent to this email")
    code, expiry = entry
    if time.time() > expiry:
        del verification_codes[request.email]
        raise HTTPException(status_code=400, detail="Verification code expired")
    if request.code.upper() != code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    db.commit()
    del verification_codes[request.email]
    return {"msg": "Email verified successfully"}