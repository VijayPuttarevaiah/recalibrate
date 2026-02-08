from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from utils.db_session import get_db
from services.auth_service import AuthService
from utils.logging_config import LogManager

logger = LogManager.get_logger()

router = APIRouter()
# OAuth2 scheme for extracting the Bearer token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Invalidates the current user's token by adding it to a blacklist.
    """
    logger.info("POST /logout request received")
    auth_service = AuthService(db)
    result = auth_service.logout_user(token, db)
    logger.info("Logout process completed")
    return result
