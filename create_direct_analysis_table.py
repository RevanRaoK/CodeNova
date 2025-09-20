#!/usr/bin/env python3
"""
Database migration script to create the DirectAnalysis table.
Run this script to add the new table for direct code analysis.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models.analysis import DirectAnalysis
from app.core.database import Base

def create_direct_analysis_table():
    """Create the DirectAnalysis table if it doesn't exist."""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    print("Creating DirectAnalysis table...")
    
    try:
        # Create the table
        Base.metadata.create_all(bind=engine, tables=[DirectAnalysis.__table__])
        print("✅ DirectAnalysis table created successfully!")
        
        # Verify the table was created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'direct_analyses'
            """))
            
            if result.fetchone():
                print("✅ Table verification successful!")
            else:
                print("❌ Table verification failed!")
                
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        return False
    
    return True

def add_relationship_to_users():
    """Add the relationship column if needed (this is handled by SQLAlchemy relationships)."""
    print("✅ User relationships are handled automatically by SQLAlchemy.")
    return True

if __name__ == "__main__":
    print("=== DirectAnalysis Table Migration ===")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    success = create_direct_analysis_table()
    if success:
        add_relationship_to_users()
        print("\n🎉 Migration completed successfully!")
        print("\nYou can now use the enhanced analysis endpoints:")
        print("- POST /api/v1/analysis/analyze-code")
        print("- GET /api/v1/analysis/direct/history")
        print("- GET /api/v1/analysis/direct/stats")
        print("- GET /api/v1/analysis/direct/{analysis_id}")
        print("- DELETE /api/v1/analysis/direct/{analysis_id}")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)