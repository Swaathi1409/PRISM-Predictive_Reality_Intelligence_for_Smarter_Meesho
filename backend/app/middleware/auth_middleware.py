"""
auth_middleware.py — FastAPI dependency for route protection.

Usage in any route:
  from app.middleware.auth_middleware import get_current_user_id, optional_user_id

  @router.post("/prism/analyze")
  def analyze(request: PrismRequest, user_id: str = Depends(get_current_user_id)):
      ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.auth_service import decode_token
from jose import JWTError

bearer_scheme = HTTPBearer()
optional_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> str:
    """Strict auth — raises 401 if not logged in."""
    try:
        return decode_token(credentials.credentials)
    except (JWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def optional_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(optional_bearer),
) -> str | None:
    """Optional auth — returns None if not logged in, no error."""
    if not credentials:
        return None
    try:
        return decode_token(credentials.credentials)
    except:
        return None
