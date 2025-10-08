#!/usr/bin/env python3
"""
Migration script to add profile columns to the users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def add_profile_columns():
    """Add profile-related columns to the users table"""
    
    # SQL commands to add the new columns
    migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100);", 
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title VARCHAR(200);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio VARCHAR(1000);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS programming_languages VARCHAR(500);"
    ]
    
    try:
        with engine.connect() as connection:
            for migration in migrations:
                print(f"Executing: {migration}")
                connection.execute(text(migration))
                connection.commit()
        
        print("✅ Successfully added profile columns to users table")
        
    except Exception as e:
        print(f"❌ Error adding profile columns: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Adding profile columns to users table...")
    success = add_profile_columns()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)