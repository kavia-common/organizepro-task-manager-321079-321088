"""
Database configuration and session management.

Uses environment variables defined in the backend container .env:
- POSTGRES_URL (preferred, full SQLAlchemy URL)
- POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT (fallback pieces)

We intentionally avoid hardcoding secrets/config.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def _build_database_url() -> str:
    """Build a SQLAlchemy database URL from environment variables."""
    url = os.getenv("POSTGRES_URL")
    if url:
        # Allow quotes in .env values (common in templates)
        return url.strip().strip('"').strip("'")

    user = (os.getenv("POSTGRES_USER") or "").strip().strip('"').strip("'")
    password = (os.getenv("POSTGRES_PASSWORD") or "").strip().strip('"').strip("'")
    db = (os.getenv("POSTGRES_DB") or "").strip().strip('"').strip("'")
    port = (os.getenv("POSTGRES_PORT") or "").strip().strip('"').strip("'")

    # Host is localhost in this template; if your deployment differs, provide POSTGRES_URL.
    host = "localhost"
    if not all([user, password, db, port]):
        raise RuntimeError(
            "Database configuration missing. Set POSTGRES_URL or "
            "POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_PORT in .env."
        )
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


_ENGINE = None
_SessionLocal: Optional[sessionmaker] = None


def _get_engine():
    """Create (if needed) and return the SQLAlchemy Engine."""
    global _ENGINE, _SessionLocal
    if _ENGINE is None:
        database_url = _build_database_url()
        _ENGINE = create_engine(
            database_url,
            pool_pre_ping=True,
        )
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)
    return _ENGINE


# PUBLIC_INTERFACE
def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy Session and closes it afterwards."""
    _get_engine()
    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for scripts/tests: opens session, commits/rollbacks automatically."""
    _get_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
