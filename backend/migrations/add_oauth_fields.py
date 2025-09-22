"""
Database migration to add OAuth fields to users table
Run this script to update your database schema for OAuth support
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def upgrade_database():
    """Add OAuth fields to users table"""
    db = SessionLocal()
    
    try:
        print("Adding OAuth fields to users table...")
        
        # Add OAuth fields
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR(50),
            ADD COLUMN IF NOT EXISTS oauth_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS oauth_email_verified BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS profile_picture_url VARCHAR(512);
        """))
        
        # Make hashed_password nullable for OAuth users
        db.execute(text("""
            ALTER TABLE users 
            ALTER COLUMN hashed_password DROP NOT NULL;
        """))
        
        # Add unique constraint for OAuth users
        db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS unique_oauth_user 
            ON users (oauth_provider, oauth_id) 
            WHERE oauth_provider IS NOT NULL AND oauth_id IS NOT NULL;
        """))
        
        db.commit()
        print("✅ OAuth fields added successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def downgrade_database():
    """Remove OAuth fields from users table"""
    db = SessionLocal()
    
    try:
        print("Removing OAuth fields from users table...")
        
        # Drop unique constraint
        db.execute(text("DROP INDEX IF EXISTS unique_oauth_user;"))
        
        # Remove OAuth fields
        db.execute(text("""
            ALTER TABLE users 
            DROP COLUMN IF EXISTS oauth_provider,
            DROP COLUMN IF EXISTS oauth_id,
            DROP COLUMN IF EXISTS oauth_email_verified,
            DROP COLUMN IF EXISTS profile_picture_url;
        """))
        
        # Make hashed_password NOT NULL again (be careful with existing OAuth users)
        db.execute(text("""
            ALTER TABLE users 
            ALTER COLUMN hashed_password SET NOT NULL;
        """))
        
        db.commit()
        print("✅ OAuth fields removed successfully!")
        
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='OAuth database migration')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')
    
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade_database()
    else:
        upgrade_database()