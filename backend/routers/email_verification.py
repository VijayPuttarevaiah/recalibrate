# Import necessary modules from FastAPI, Pydantic, SQLAlchemy, and utilities
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import random, string, time
from utils.email_sender import send_email
from sqlalchemy.orm import Session
from models.user_models import User
from utils.db_session import DBSession

# Initialize the router for email verification endpoints
router = APIRouter()

# In-memory store: {email: (code, expiry_time)} used briefly for demonstration
# In production, this should be in Redis or a database table
verification_codes = {}
CODE_EXPIRY_SECONDS = 70  # Codes expire after 70 seconds

# Helper function to generate a random alphanumeric verification code
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Schema for requesting a verification code
class SendCodeRequest(BaseModel):
    email: EmailStr

# Schema for verifying a code
class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

# Dependency to get a local database session
def get_db():
    db = DBSession().SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint to generate and send a verification code to a user's email
@router.post("/send-code")
def send_code(request: SendCodeRequest):
   
    code = generate_code()
    expiry = time.time() + CODE_EXPIRY_SECONDS
    # Store the code and its expiry time in the in-memory store
    verification_codes[request.email] = (code, expiry)
    # Prepare and send the email using the email_sender utility
    subject = "Your Verification Code"
    body = f"Your verification code is: {code}"
    try:
        send_email(request.email, subject, body)
    except Exception as e:
        # Raise an error if the email fails to send
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    # Return a success message
    return {"msg": "Verification code sent to email"}

# Endpoint to verify the user's email using the code provided
@router.post("/verify")
def verify_email(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    # Retrieve the stored code and expiry for the given email
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