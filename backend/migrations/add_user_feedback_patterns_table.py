"""
Migration to add user_feedback_patterns table for caching feedback pattern analysis.

This table stores aggregated feedback patterns per user to optimize personalized AI suggestions.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()


def run_migration():
    """Run the migration to create user_feedback_patterns table."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_engine(database_url)
    
    print("Creating user_feedback_patterns table...")
    
    # Create table using raw SQL to avoid foreign key resolution issues
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS user_feedback_patterns (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        category VARCHAR(100) NOT NULL,
        severity VARCHAR(20) NOT NULL,
        acceptance_rate FLOAT NOT NULL DEFAULT 0.0,
        total_feedback_count INTEGER NOT NULL DEFAULT 0,
        accepted_count INTEGER NOT NULL DEFAULT 0,
        rejected_count INTEGER NOT NULL DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, category, severity)
    );
    """
    
    # Create indexes
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_user_feedback_patterns_user ON user_feedback_patterns(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_feedback_patterns_category ON user_feedback_patterns(category);",
        "CREATE INDEX IF NOT EXISTS idx_user_feedback_patterns_severity ON user_feedback_patterns(severity);",
        "CREATE INDEX IF NOT EXISTS idx_user_feedback_patterns_user_category ON user_feedback_patterns(user_id, category);",
        "CREATE INDEX IF NOT EXISTS idx_user_feedback_patterns_acceptance ON user_feedback_patterns(acceptance_rate);",
        "CREATE INDEX IF NOT EXISTS idx_user_feedback_patterns_updated ON user_feedback_patterns(last_updated);"
    ]
    
    with engine.connect() as conn:
        # Create table
        conn.execute(text(create_table_sql))
        conn.commit()
        print("✓ user_feedback_patterns table created successfully")
        
        # Create indexes
        for idx_sql in create_indexes_sql:
            conn.execute(text(idx_sql))
        conn.commit()
        print(f"✓ Created {len(create_indexes_sql)} indexes")
        
        # Verify table creation
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "user_feedback_patterns" in tables:
            print("✓ Migration verified: user_feedback_patterns table exists")
            
            # Show columns
            columns = inspector.get_columns("user_feedback_patterns")
            print(f"✓ Table has {len(columns)} columns:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            # Show indexes
            indexes = inspector.get_indexes("user_feedback_patterns")
            print(f"✓ Table has {len(indexes)} indexes:")
            for idx in indexes:
                print(f"  - {idx['name']}: {idx['column_names']}")
        else:
            print("✗ Migration failed: user_feedback_patterns table not found")
            return False
        
        return True


if __name__ == "__main__":
    try:
        success = run_migration()
        if success:
            print("\n✓ Migration completed successfully!")
        else:
            print("\n✗ Migration failed!")
            exit(1)
    except Exception as e:
        print(f"\n✗ Migration error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
