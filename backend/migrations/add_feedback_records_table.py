"""
Database migration to add feedback_records table for user feedback collection
Run this script to create the feedback_records table with proper validation and relationships
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def upgrade_database():
    """Create feedback_records table with validation and relationships"""
    db = SessionLocal()
    
    try:
        print("Creating feedback_records table...")
        
        # Create feedback_records table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS feedback_records (
                id SERIAL PRIMARY KEY,
                issue_id VARCHAR(64) NOT NULL,
                user_id INTEGER NOT NULL,
                feedback_type VARCHAR(20) NOT NULL,
                feedback_value INTEGER NOT NULL,
                feedback_comment TEXT,
                modified_suggestion TEXT,
                context_data JSON,
                user_experience_level VARCHAR(20),
                code_review_context VARCHAR(50),
                is_validated BOOLEAN DEFAULT FALSE,
                validation_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT fk_feedback_issue_id 
                    FOREIGN KEY (issue_id) 
                    REFERENCES issues(id) 
                    ON DELETE CASCADE,
                    
                CONSTRAINT fk_feedback_user_id 
                    FOREIGN KEY (user_id) 
                    REFERENCES users(id) 
                    ON DELETE CASCADE,
                    
                CONSTRAINT chk_feedback_type 
                    CHECK (feedback_type IN ('accept', 'reject', 'modify', 'ignore')),
                    
                CONSTRAINT chk_feedback_value 
                    CHECK (feedback_value IN (-1, 0, 1)),
                    
                CONSTRAINT chk_experience_level 
                    CHECK (user_experience_level IS NULL OR 
                           user_experience_level IN ('beginner', 'intermediate', 'expert')),
                           
                CONSTRAINT chk_review_context 
                    CHECK (code_review_context IS NULL OR 
                           code_review_context IN ('personal', 'team', 'production', 'learning'))
            );
        """))
        
        # Create indexes for performance
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_id ON feedback_records (id);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_issue_id ON feedback_records (issue_id);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback_records (user_id);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback_records (feedback_type);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback_records (created_at);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_validated ON feedback_records (is_validated);
        """))
        
        # Composite indexes for common queries
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_issue_user 
            ON feedback_records (issue_id, user_id);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_type_value 
            ON feedback_records (feedback_type, feedback_value);
        """))
        
        # Unique constraint to prevent duplicate feedback from same user on same issue
        db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS unique_user_issue_feedback 
            ON feedback_records (issue_id, user_id);
        """))
        
        # Create trigger for updated_at timestamp
        db.execute(text("""
            CREATE OR REPLACE FUNCTION update_feedback_records_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        db.execute(text("""
            DROP TRIGGER IF EXISTS trigger_feedback_records_updated_at ON feedback_records;
            CREATE TRIGGER trigger_feedback_records_updated_at
                BEFORE UPDATE ON feedback_records
                FOR EACH ROW
                EXECUTE FUNCTION update_feedback_records_updated_at();
        """))
        
        db.commit()
        print("✅ Feedback records table created successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def downgrade_database():
    """Drop feedback_records table and related objects"""
    db = SessionLocal()
    
    try:
        print("Dropping feedback_records table...")
        
        # Drop trigger and function
        db.execute(text("DROP TRIGGER IF EXISTS trigger_feedback_records_updated_at ON feedback_records;"))
        db.execute(text("DROP FUNCTION IF EXISTS update_feedback_records_updated_at();"))
        
        # Drop table (indexes and constraints will be dropped automatically)
        db.execute(text("DROP TABLE IF EXISTS feedback_records CASCADE;"))
        
        db.commit()
        print("✅ Feedback records table dropped successfully!")
        
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Feedback records table database migration')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')
    
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade_database()
    else:
        upgrade_database()