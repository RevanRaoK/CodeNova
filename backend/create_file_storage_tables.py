"""
Create file storage tables in the database.

This script ensures that the stored_files table exists for Digital Ocean Spaces integration.
"""

from app.core.database import engine, Base
from app.models.file_storage import StoredFile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all tables defined in the models."""
    try:
        logger.info("Creating file storage tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✓ File storage tables created successfully!")
        
        # Verify the table exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'stored_files' in tables:
            logger.info("✓ stored_files table verified")
            
            # Get column info
            columns = inspector.get_columns('stored_files')
            logger.info(f"  - Table has {len(columns)} columns")
            for col in columns:
                logger.info(f"    - {col['name']}: {col['type']}")
        else:
            logger.error("✗ stored_files table not found")
            
    except Exception as e:
        logger.error(f"✗ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    create_tables()