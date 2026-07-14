"""
database.py — SQLAlchemy engine and session factory for PRISM.

WHY SQLAlchemy (MIT License):
Database-agnostic ORM. Works identically on SQLite in development and PostgreSQL
in production. The DATABASE_URL environment variable is the only thing that changes
between environments — no code changes required.

WHY Alembic (MIT License):
Tracks schema changes as versioned migration scripts. Judges running the project
get a reproducible, clean database without manually running SQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

# SQLite requires check_same_thread=False for FastAPI's multi-threaded request handling
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=(settings.environment == "development"),
    pool_pre_ping=True,  # auto-reconnect dropped connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Creates all tables on startup if they do not exist."""
    from app.models.orm_models import Session, Recommendation, AgentLog  # noqa: F401
    Base.metadata.create_all(bind=engine)
