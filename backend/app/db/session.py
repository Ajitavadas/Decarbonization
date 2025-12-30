"""
Database session dependency injection
"""

from typing import Generator
from app.db.base import SessionLocal


def get_db() -> Generator:
    """
    Database session dependency
    Creates a new session for each request and closes it after
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
