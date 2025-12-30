"""
Database initialization and seed data
"""

from sqlalchemy.orm import Session
from app.db.base import engine, Base
from app.models import user, organization, project, activity, batch_job, custom_mapping


def init_db(db: Session) -> None:
    """
    Initialize database with tables and seed data
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Add seed data here if needed
    print("Database initialized successfully")


if __name__ == "__main__":
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
