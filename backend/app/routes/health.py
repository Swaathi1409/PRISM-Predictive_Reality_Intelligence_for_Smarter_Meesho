"""
health.py — Health check endpoint for PRISM.

Used by Docker healthcheck and by judges to verify the system is running.
Returns DB connectivity status and whether the Groq client is configured.
"""

from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.models.database import engine

router = APIRouter(tags=["health"])


@router.get("/health", response_model=dict)
def health_check():
    """
    Returns the health status of the PRISM API.
    - db_connected: True if SQLite/PostgreSQL is reachable
    - api_key_configured: True if GROQ_API_KEY is set (does not test validity)
    - status: 'healthy' if all checks pass, 'degraded' if any fail
    """
    # Test DB connection
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Verify API key is set and non-trivial
    api_key_set = bool(
        settings.groq_api_key
        and settings.groq_api_key != "not_set"
        and settings.groq_api_key != "your_key_here"
        and len(settings.groq_api_key) > 10
    )

    return {
        "status": "healthy" if db_ok and api_key_set else "degraded",
        "version": "1.0.0",
        "environment": settings.environment,
        "db_connected": db_ok,
        "api_key_configured": api_key_set,
        "llm_model": settings.llm_model,
    }
