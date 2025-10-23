#!/usr/bin/env python3
"""
Migration script to add all missing columns to the users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def add_missing_columns():
    """Add all missing columns to the users table"""
    
    # SQL commands to add the new columns
    migrations = [
        # Add team_id if not exists (already done but included for completeness)
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS team_id VARCHAR(36);",
        "CREATE INDEX IF NOT EXISTS idx_users_team_id ON users(team_id);",
        
        # Add preferences column (JSON type)
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}'::jsonb;",
        
        # Add profile columns if not exists
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title VARCHAR(200);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio VARCHAR(1000);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS programming_languages VARCHAR(500);",
        
        # Add OAuth columns if not exists
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR(50);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_id VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_email_verified BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture_url VARCHAR(512);",
        
        # Add timestamp columns if not exists
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
    ]
    
    try:
        with engine.connect() as connection:
            print("Adding missing columns to users table...")
            print("=" * 50)
            
            for migration in migrations:
                print(f"Executing: {migration[:80]}...")
                connection.execute(text(migration))
                connection.commit()
            
            print("=" * 50)
            print("✅ Successfully added all missing columns to users table")
        
    except Exception as e:
        print(f"❌ Error adding columns: {e}")
        return False
    
    return True

def verify_columns():
    """Verify that all columns exist"""
    
    try:
        with engine.connect() as connection:
            # Query to get all columns in users table
            result = connection.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            
            print("\n" + "=" * 50)
            print("Current users table schema:")
            print("=" * 50)
            
            for col in columns:
                print(f"  {col[0]:<30} {col[1]}")
            
            print("=" * 50)
            
            # Check for required columns
            required_columns = [
                'id', 'email', 'full_name', 'hashed_password', 'role',
                'is_active', 'is_verified', 'team_id', 'preferences',
                'first_name', 'last_name', 'job_title', 'bio',
                'programming_languages', 'oauth_provider', 'oauth_id',
                'oauth_email_verified', 'profile_picture_url',
                'last_login', 'created_at', 'updated_at'
            ]
            
            existing_columns = [col[0] for col in columns]
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            if missing_columns:
                print(f"\n⚠️  Missing columns: {', '.join(missing_columns)}")
                return False
            else:
                print("\n✅ All required columns are present!")
                return True
            
    except Exception as e:
        print(f"❌ Error verifying columns: {e}")
        return False

if __name__ == "__main__":
    print("CodeNova Database Migration - Add Missing User Columns")
    print("=" * 60)
    
    # Add missing columns
    success = add_missing_columns()
    
    if success:
        # Verify columns
        verify_columns()
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("You can now restart your backend server and try logging in.")
        print("=" * 60)
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)
