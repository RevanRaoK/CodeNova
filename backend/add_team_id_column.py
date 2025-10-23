#!/usr/bin/env python3
"""
Migration script to add team_id column to the users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def add_team_id_column():
    """Add team_id column to the users table"""
    
    # SQL commands to add the new column
    migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS team_id VARCHAR(36);",
        "CREATE INDEX IF NOT EXISTS idx_users_team_id ON users(team_id);"
    ]
    
    try:
        with engine.connect() as connection:
            for migration in migrations:
                print(f"Executing: {migration}")
                connection.execute(text(migration))
                connection.commit()
        
        print("✅ Successfully added team_id column to users table")
        
    except Exception as e:
        print(f"❌ Error adding team_id column: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Adding team_id column to users table...")
    success = add_team_id_column()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)