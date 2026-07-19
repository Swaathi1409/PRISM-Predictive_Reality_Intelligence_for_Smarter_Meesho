"""
auth_service.py — JWT + bcrypt authentication for PRISM.

WHY bcrypt (passlib, MIT License):
Industry standard for password hashing. Automatically salted.
Even if DB is compromised, passwords cannot be reversed.

WHY JWT (python-jose, MIT License):
Stateless tokens. No session table needed. Token carries user_id.
7-day expiry means judges stay logged in across the demo day.

WHY no Firebase/OAuth:
This is a hackathon prototype. A local JWT system is faster to build,
has zero external dependencies, works offline, and is fully auditable.
The UX is identical to a real auth system for demo purposes.
"""

import uuid
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from app.models.orm_models import User, UserMemory
from app.config import settings

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str:
    """Returns user_id from token or raises JWTError."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    user_id = payload.get("sub")
    if not user_id:
        raise JWTError("Invalid token")
    return user_id


def register_user(db: Session, email: str, name: str, password: str) -> dict:
    """Create new user + empty memory record."""
    # Check email exists
    existing = db.query(User).filter(User.email == email.lower().strip()).first()
    if existing:
        raise ValueError("An account with this email already exists.")

    # Validate
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    if len(name.strip()) < 2:
        raise ValueError("Please enter your full name.")

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=email.lower().strip(),
        name=name.strip(),
        hashed_password=hash_password(password),
    )
    db.add(user)

    # Create empty memory record
    memory = UserMemory(
        user_id=user_id,
        searched_categories=[],
        preferred_price_range=[0, 50000],
        life_events_history=[],
        liked_product_ids=[],
        disliked_categories=[],
        location_hints=[],
        persona_tags=[],
        session_count=0,
    )
    db.add(memory)
    db.commit()

    token = create_access_token(user_id)
    return {"user_id": user_id, "name": name, "email": email, "token": token}


def login_user(db: Session, email: str, password: str) -> dict:
    """Verify credentials and return token."""
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Incorrect email or password.")

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(user.id)

    # Get memory for welcome back message
    memory = db.query(UserMemory).filter(UserMemory.user_id == user.id).first()
    session_count = memory.session_count if memory else 0

    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "token": token,
        "session_count": session_count,
        "last_intent": memory.last_intent if memory else None,
    }


def get_current_user(token: str, db: Session) -> User:
    """FastAPI dependency — decode token and return User object."""
    try:
        user_id = decode_token(token)
    except JWTError:
        return None
    return db.query(User).filter(User.id == user_id).first()
