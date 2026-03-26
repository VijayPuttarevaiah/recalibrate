from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.token_schemas import TokenRefresh, RefreshTokenResponse
from services.auth_service import AuthService
from utils.db_session import get_db
from utils.logging_config import LogManager

logger = LogManager.get_logger()

router = APIRouter(prefix="/refresh", tags=["authentication"])


@router.post("", response_model=RefreshTokenResponse)
def refresh_token(
    refresh_request: TokenRefresh,
    db: Session = Depends(get_db)
) -> RefreshTokenResponse:
    """
    Refresh access token using a valid refresh token.
    
    This endpoint accepts a refresh token and returns a new access token
    along with a new refresh token (token rotation).
    
    Args:
        refresh_request: Request body containing the refresh token
        db: Database session
        
    Returns:
        RefreshTokenResponse with new access_token, refresh_token, and token_type
        
    Raises:
        HTTPException 401: If refresh token is invalid, expired, or revoked
        HTTPException 400: If request format is invalid
    """
    logger.info("Refresh token endpoint called")
    
    try:
        auth_service = AuthService(db)
        response = auth_service.refresh_access_token(refresh_request.refresh_token)
        return RefreshTokenResponse(**response)
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., invalid token)
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while refreshing the token"
        )
