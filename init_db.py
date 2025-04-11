import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base
from app.models import *  # Import all models

def init_db():
    """Initialize the database with all tables."""
    print("Creating database tables...")
    
    # Create a synchronous engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
