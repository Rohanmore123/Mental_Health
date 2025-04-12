"""
Migration script to add extracted_keywords column to chat_messages table
"""
from sqlalchemy import create_engine, text
from app.config import settings

def run_migration():
    """
    Run the migration to add extracted_keywords column to chat_messages table
    """
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Check if column already exists
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' 
            AND column_name = 'extracted_keywords'
        """))
        column_exists = result.fetchone() is not None
    
    # Add column if it doesn't exist
    if not column_exists:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE chat_messages 
                ADD COLUMN extracted_keywords JSONB
            """))
            conn.commit()
            print("Added extracted_keywords column to chat_messages table")
    else:
        print("extracted_keywords column already exists in chat_messages table")

if __name__ == "__main__":
    run_migration()
