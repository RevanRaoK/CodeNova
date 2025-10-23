"""
Migration to add gemini_api_key field to users table for storing encrypted API keys.

This migration adds support for users to provide their own Gemini API keys.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, Column, String, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.users import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Add gemini_api_key column to users table."""
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        logger.info("Starting migration: add_gemini_api_key_field")
        
        # Check if column already exists
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='gemini_api_key'
        """))
        
        if result.fetchone():
            logger.info("Column 'gemini_api_key' already exists in users table")
            return
        
        # Add gemini_api_key column
        logger.info("Adding gemini_api_key column to users table...")
        session.execute(text("""
            ALTER TABLE users 
            ADD COLUMN gemini_api_key VARCHAR(512)
        """))
        
        session.commit()
        logger.info("Successfully added gemini_api_key column")
        
        # Verify the column was added
        result = session.execute(text("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='gemini_api_key'
        """))
        
        column_info = result.fetchone()
        if column_info:
            logger.info(f"Verified column: {column_info[0]} ({column_info[1]}({column_info[2]}))")
        else:
            logger.error("Failed to verify column was added")
        
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_migration()
