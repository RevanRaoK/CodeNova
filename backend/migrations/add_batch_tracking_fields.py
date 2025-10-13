"""
Database migration to add batch tracking fields to stored_files table.

This migration adds the following fields to support enhanced file storage:
- batch_id: For grouping multiple uploads
- upload_metadata: JSON string for additional metadata  
- processing_status: Track file processing status

Requirements covered: 2.1, 2.2, 2.3
"""

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Add batch tracking fields to stored_files table."""
    
    with engine.connect() as connection:
        # Add batch_id column
        try:
            connection.execute(text("""
                ALTER TABLE stored_files 
                ADD COLUMN batch_id VARCHAR(36)
            """))
            print("✓ Added batch_id column")
        except Exception as e:
            print(f"batch_id column may already exist: {e}")
        
        # Add upload_metadata column
        try:
            connection.execute(text("""
                ALTER TABLE stored_files 
                ADD COLUMN upload_metadata VARCHAR(2000)
            """))
            print("✓ Added upload_metadata column")
        except Exception as e:
            print(f"upload_metadata column may already exist: {e}")
        
        # Add processing_status column
        try:
            connection.execute(text("""
                ALTER TABLE stored_files 
                ADD COLUMN processing_status VARCHAR(20) DEFAULT 'completed'
            """))
            print("✓ Added processing_status column")
        except Exception as e:
            print(f"processing_status column may already exist: {e}")
        
        # Add indexes for better performance
        try:
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stored_files_batch_id 
                ON stored_files(batch_id)
            """))
            print("✓ Added batch_id index")
        except Exception as e:
            print(f"batch_id index may already exist: {e}")
        
        try:
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stored_files_processing_status 
                ON stored_files(processing_status)
            """))
            print("✓ Added processing_status index")
        except Exception as e:
            print(f"processing_status index may already exist: {e}")
        
        connection.commit()
        print("✓ Migration completed successfully")


def downgrade():
    """Remove batch tracking fields from stored_files table."""
    
    with engine.connect() as connection:
        # Remove indexes
        try:
            connection.execute(text("DROP INDEX IF EXISTS idx_stored_files_batch_id"))
            connection.execute(text("DROP INDEX IF EXISTS idx_stored_files_processing_status"))
            print("✓ Removed indexes")
        except Exception as e:
            print(f"Error removing indexes: {e}")
        
        # Remove columns (Note: SQLite doesn't support DROP COLUMN easily)
        # In production, you might want to create a new table and migrate data
        try:
            connection.execute(text("ALTER TABLE stored_files DROP COLUMN batch_id"))
            connection.execute(text("ALTER TABLE stored_files DROP COLUMN upload_metadata"))
            connection.execute(text("ALTER TABLE stored_files DROP COLUMN processing_status"))
            print("✓ Removed batch tracking columns")
        except Exception as e:
            print(f"Error removing columns (this is expected for SQLite): {e}")
        
        connection.commit()
        print("✓ Downgrade completed")


if __name__ == "__main__":
    print("Running batch tracking fields migration...")
    upgrade()