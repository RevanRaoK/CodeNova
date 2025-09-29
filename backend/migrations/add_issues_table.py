"""
Database migration to add issues table for AST feedback pipeline
Run this script to create the issues table with proper indexing and relationships
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def upgrade_database():
    """Create issues table with proper indexing and relationships"""
    db = SessionLocal()
    
    try:
        print("Creating issues table...")
        
        # Create issues table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS issues (
                id VARCHAR(64) PRIMARY KEY,
                analysis_id VARCHAR(36) NOT NULL,
                pattern_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                category VARCHAR(50),
                location JSON NOT NULL,
                suggestion_text TEXT NOT NULL,
                code_context TEXT NOT NULL,
                original_code TEXT,
                suggested_fix TEXT,
                ast_node_type VARCHAR(100),
                ast_metadata JSON,
                status VARCHAR(20) DEFAULT 'active',
                confidence_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                
                CONSTRAINT fk_issues_analysis_id 
                    FOREIGN KEY (analysis_id) 
                    REFERENCES direct_analyses(id) 
                    ON DELETE CASCADE
            );
        """))
        
        # Create indexes for performance
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_issues_id ON issues (id);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_issues_analysis_id ON issues (analysis_id);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_issues_pattern_type ON issues (pattern_type);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues (severity);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_issues_category ON issues (category);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_issues_status ON issues (status);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_issues_created_at ON issues (created_at);
        """))
        
        # Composite indexes for common queries
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_issues_analysis_pattern 
            ON issues (analysis_id, pattern_type);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_issues_severity_status 
            ON issues (severity, status);
        """))
        
        # Create trigger for updated_at timestamp
        db.execute(text("""
            CREATE OR REPLACE FUNCTION update_issues_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        db.execute(text("""
            DROP TRIGGER IF EXISTS trigger_issues_updated_at ON issues;
            CREATE TRIGGER trigger_issues_updated_at
                BEFORE UPDATE ON issues
                FOR EACH ROW
                EXECUTE FUNCTION update_issues_updated_at();
        """))
        
        db.commit()
        print("✅ Issues table created successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def downgrade_database():
    """Drop issues table and related objects"""
    db = SessionLocal()
    
    try:
        print("Dropping issues table...")
        
        # Drop trigger and function
        db.execute(text("DROP TRIGGER IF EXISTS trigger_issues_updated_at ON issues;"))
        db.execute(text("DROP FUNCTION IF EXISTS update_issues_updated_at();"))
        
        # Drop table (indexes will be dropped automatically)
        db.execute(text("DROP TABLE IF EXISTS issues CASCADE;"))
        
        db.commit()
        print("✅ Issues table dropped successfully!")
        
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Issues table database migration')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')
    
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade_database()
    else:
        upgrade_database()