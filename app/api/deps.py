from typing import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.users import User
from app.services.auth import get_current_active_user

def get_db() -> Generator:
    """
    Get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
