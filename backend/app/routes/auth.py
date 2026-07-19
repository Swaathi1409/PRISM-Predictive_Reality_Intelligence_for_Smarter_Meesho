"""
auth.py — Register, login, logout, profile, and memory endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.models.database import get_db
from app.services.auth_service import register_user, login_user
from app.services.memory_service import get_user_memory, record_product_choice
from app.middleware.auth_middleware import get_current_user_id
from app.models.orm_models import User
from app.utils.logger import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ProductChoiceRequest(BaseModel):
    product_id: str


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        result = register_user(db, request.email, request.name, request.password)
        logger.info(f"New user registered: {request.email}")
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = login_user(db, request.email, request.password)
        logger.info(f"User logged in: {request.email}")
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    memory = get_user_memory(db, user_id)
    return {
        "user_id": user_id,
        "name": user.name,
        "email": user.email,
        "memory": memory,
    }


@router.get("/memory")
def get_memory(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Expose user memory so judges can see personalisation is real."""
    memory = get_user_memory(db, user_id)
    return {"user_id": user_id, "memory": memory}


@router.post("/choose-product")
def choose_product(
    body: ProductChoiceRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Called when user taps 'Choose this' on a product card."""
    record_product_choice(db, user_id, body.product_id)
    return {"success": True, "message": "Product preference saved to your memory."}


@router.post("/logout")
def logout():
    """Client-side logout — just delete the token. Endpoint for completeness."""
    return {"success": True, "message": "Logged out successfully."}
