#!/usr/bin/env python3
"""
Check user using backend's own database connection
Usage: python check_user_simple.py
"""

import os
import sys
from pathlib import Path

# Set PYTHONPATH to include the backend directory
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment to development if not set
os.environ.setdefault('ENVIRONMENT', 'development')

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    
    print("🔍 Checking user with backend database connection...")
    print("==================================================")
    
    # Use the same database URL as the backend
    print(f"Database URL: {settings.DATABASE_URL}")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        # Check user
        result = db.execute(text("""
            SELECT id, email, full_name, role, is_active, is_verified, 
                   CASE WHEN hashed_password IS NOT NULL THEN 'Yes' ELSE 'No' END as has_password,
                   created_at
            FROM users 
            WHERE email = :email
        """), {"email": "revankokkirala@gmail.com"})
        
        user = result.fetchone()
        
        if user:
            print("✅ User found:")
            print(f"  - ID: {user.id}")
            print(f"  - Email: {user.email}")
            print(f"  - Name: {user.full_name}")
            print(f"  - Role: {user.role}")
            print(f"  - Active: {user.is_active}")
            print(f"  - Verified: {user.is_verified}")
            print(f"  - Has Password: {user.has_password}")
            print(f"  - Created: {user.created_at}")
            
            if user.role == 'admin' and user.is_active:
                print("\\n✅ User should be able to access admin panel!")
            elif user.role != 'admin':
                print(f"\\n❌ User role is '{user.role}', not 'admin'")
            elif not user.is_active:
                print("\\n❌ User is not active")
                
        else:
            print("❌ User not found!")
            
            # Check total users
            result = db.execute(text("SELECT COUNT(*) as count FROM users"))
            count = result.fetchone().count
            print(f"Total users in database: {count}")
            
            if count > 0:
                result = db.execute(text("SELECT email, role FROM users LIMIT 5"))
                users = result.fetchall()
                print("Sample users:")
                for user in users:
                    print(f"  - {user.email} ({user.role})")
    
    print("\\n🔧 If user exists but login fails, the issue is likely:")
    print("1. Password hash mismatch")
    print("2. Backend authentication logic issue")
    print("3. API endpoint issue")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()