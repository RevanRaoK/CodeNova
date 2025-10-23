"""
Migration to add file batch processing tables.

This migration creates the tables needed for multi-file upload batch processing:
- file_batches: Tracks batch processing jobs
- batch_files: Tracks individual files within batches
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add file batch tables."""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    db = SessionLocal()
    
    try:
        logger.info("Starting file batch tables migration...")
        
        # Create file_batches table
        create_file_batches_table = """
        CREATE TABLE IF NOT EXISTS file_batches (
            id VARCHAR(36) PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            total_files INTEGER NOT NULL,
            processed_files INTEGER DEFAULT 0,
            successful_files INTEGER DEFAULT 0,
            failed_files INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending',
            combined_results JSON,
            error_details JSON,
            processing_log JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            total_size_bytes INTEGER DEFAULT 0,
            processing_time_seconds FLOAT,
            estimated_completion_time TIMESTAMP
        );
        """
        
        # Create batch_files table
        create_batch_files_table = """
        CREATE TABLE IF NOT EXISTS batch_files (
            id VARCHAR(36) PRIMARY KEY,
            batch_id VARCHAR(36) NOT NULL REFERENCES file_batches(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            content_type VARCHAR(100),
            language VARCHAR(50),
            file_index INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            file_content TEXT,
            storage_path VARCHAR(512),
            stored_file_id VARCHAR(36),
            analysis_id VARCHAR(36),
            issues_count INTEGER DEFAULT 0,
            errors_count INTEGER DEFAULT 0,
            warnings_count INTEGER DEFAULT 0,
            suggestions_count INTEGER DEFAULT 0,
            analysis_results JSON,
            analysis_metrics JSON,
            analysis_summary TEXT,
            error_message TEXT,
            error_code VARCHAR(50),
            error_details JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_processing_at TIMESTAMP,
            completed_at TIMESTAMP,
            processing_time_seconds FLOAT
        );
        """
        
        # Create indexes for better performance
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_file_batches_user_id ON file_batches(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_file_batches_status ON file_batches(status);",
            "CREATE INDEX IF NOT EXISTS idx_file_batches_created_at ON file_batches(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_batch_files_batch_id ON batch_files(batch_id);",
            "CREATE INDEX IF NOT EXISTS idx_batch_files_status ON batch_files(status);",
            "CREATE INDEX IF NOT EXISTS idx_batch_files_file_index ON batch_files(batch_id, file_index);"
        ]
        
        # Execute table creation
        db.execute(text(create_file_batches_table))
        logger.info("Created file_batches table")
        
        db.execute(text(create_batch_files_table))
        logger.info("Created batch_files table")
        
        # Execute index creation
        for index_sql in create_indexes:
            db.execute(text(index_sql))
        
        logger.info("Created indexes for file batch tables")
        
        # Commit changes
        db.commit()
        
        logger.info("File batch tables migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()