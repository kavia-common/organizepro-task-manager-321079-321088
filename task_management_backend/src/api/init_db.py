"""Database initialization utilities (table creation)."""

from __future__ import annotations

from .db import _get_engine
from .models import Base


# PUBLIC_INTERFACE
def init_db() -> None:
    """Create database tables if they don't exist yet."""
    engine = _get_engine()
    Base.metadata.create_all(bind=engine)
