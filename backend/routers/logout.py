from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.user_models import BlacklistedToken
from utils.db_session import DBSession
from datetime import datetime, timezone

router = APIRouter()
# OAuth2 scheme for extracting the Bearer token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Dependency to provide a database session to the routes
def get_db():
    db = DBSession().SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Invalidates the current user's token by adding it to a blacklist.
    """
    # Check if this specific token is already in the blacklist database
    blacklisted = db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
    if blacklisted:
        return {"msg": "Token already blacklisted"}
    
    # Create a new entry in the BlacklistedToken table
    new_blacklisted_token = BlacklistedToken(token=token, blacklisted_on=datetime.now(timezone.utc))
    db.add(new_blacklisted_token)
    db.commit()
    
    # Return success response to the client
    return {"msg": "Successfully logged out"}
