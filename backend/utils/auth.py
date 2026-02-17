from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from utils.db_session import get_db
from models.token_models import BlacklistedToken
from config.config import Config

config = Config()
SECRET_KEY = config.config['oauth2']['secret_key']
ALGORITHM = config.config['oauth2'].get('algorithm', 'HS256')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    blacklisted = db.query(BlacklistedToken).filter(
        BlacklistedToken.token == token
    ).first()
    if blacklisted:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        email: str = payload.get("sub")
        if user_id is None or email is None:
            raise credentials_exception
        return {"user_id": user_id, "email": email}
    except JWTError:
        raise credentials_exception