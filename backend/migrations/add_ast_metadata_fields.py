"""
Database migration to add AST metadata fields to DirectAnalysis model
This migration adds the required fields for AST parsing and issue tracking functionality
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def upgrade_database():
    """Add AST metadata fields to direct_analyses table"""
    db = SessionLocal()
    
    try:
        print("Adding AST metadata fields to direct_analyses table...")
        
        # Add AST-related columns to direct_analyses table
        print("1. Adding ast_metadata column...")
        db.execute(text("""
            ALTER TABLE direct_analyses 
            ADD COLUMN IF NOT EXISTS ast_metadata JSON;
        """))
        
        print("2. Adding code_patterns column...")
        db.execute(text("""
            ALTER TABLE direct_analyses 
            ADD COLUMN IF NOT EXISTS code_patterns JSON;
        """))
        
        print("3. Adding issue_ids column...")
        db.execute(text("""
            ALTER TABLE direct_analyses 
            ADD COLUMN IF NOT EXISTS issue_ids JSON;
        """))
        
        print("4. Adding ast_processing_time column...")
        db.execute(text("""
            ALTER TABLE direct_analyses 
            ADD COLUMN IF NOT EXISTS ast_processing_time FLOAT;
        """))
        
        # Add indexes for better query performance
        print("5. Creating indexes for AST fields...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_direct_analyses_ast_processing_time ON direct_analyses (ast_processing_time);",
            "CREATE INDEX IF NOT EXISTS idx_direct_analyses_has_ast_metadata ON direct_analyses ((ast_metadata IS NOT NULL));",
            "CREATE INDEX IF NOT EXISTS idx_direct_analyses_has_patterns ON direct_analyses ((code_patterns IS NOT NULL));",
            "CREATE INDEX IF NOT EXISTS idx_direct_analyses_has_issues ON direct_analyses ((issue_ids IS NOT NULL));"
        ]
        
        for index_sql in indexes:
            db.execute(text(index_sql))
        
        # Add comments to document the new columns
        print("6. Adding column comments...")
        
        comments = [
            "COMMENT ON COLUMN direct_analyses.ast_metadata IS 'JSON containing AST parsing results and structure information';",
            "COMMENT ON COLUMN direct_analyses.code_patterns IS 'JSON containing detected code patterns from AST analysis';",
            "COMMENT ON COLUMN direct_analyses.issue_ids IS 'JSON array containing generated unique issue IDs for tracking';",
            "COMMENT ON COLUMN direct_analyses.ast_processing_time IS 'Processing time in seconds for AST operations';"
        ]
        
        for comment_sql in comments:
            db.execute(text(comment_sql))
        
        db.commit()
        print("✅ AST metadata fields added successfully to direct_analyses table!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def downgrade_database():
    """Remove AST metadata fields from direct_analyses table"""
    db = SessionLocal()
    
    try:
        print("Removing AST metadata fields from direct_analyses table...")
        
        # Drop indexes first
        print("1. Dropping AST-related indexes...")
        indexes_to_drop = [
            "DROP INDEX IF EXISTS idx_direct_analyses_ast_processing_time;",
            "DROP INDEX IF EXISTS idx_direct_analyses_has_ast_metadata;",
            "DROP INDEX IF EXISTS idx_direct_analyses_has_patterns;",
            "DROP INDEX IF EXISTS idx_direct_analyses_has_issues;"
        ]
        
        for index_sql in indexes_to_drop:
            db.execute(text(index_sql))
        
        # Remove columns
        print("2. Removing AST metadata columns...")
        columns_to_drop = [
            "ALTER TABLE direct_analyses DROP COLUMN IF EXISTS ast_metadata;",
            "ALTER TABLE direct_analyses DROP COLUMN IF EXISTS code_patterns;",
            "ALTER TABLE direct_analyses DROP COLUMN IF EXISTS issue_ids;",
            "ALTER TABLE direct_analyses DROP COLUMN IF EXISTS ast_processing_time;"
        ]
        
        for column_sql in columns_to_drop:
            db.execute(text(column_sql))
        
        db.commit()
        print("✅ AST metadata fields removed successfully from direct_analyses table!")
        
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AST metadata fields migration for DirectAnalysis')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')
    
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade_database()
    else:
        upgrade_database()