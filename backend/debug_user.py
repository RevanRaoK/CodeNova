#!/usr/bin/env python3
"""
Debug script to check user authentication
Usage: python debug_user.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

try:
    from app.core.config import settings
    from app.models.user import User
    from app.db.database import get_db_url
    from app.services.auth_service import AuthService
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def debug_authentication():
    print("🔍 Debugging user authentication...")
    print("==================================")
    
    # Database connection
    try:
        database_url = get_db_url()
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        print(f"📡 Connected to database")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test credentials
    test_email = "revankokkirala@gmail.com"
    test_password = "Test@123"
    
    with SessionLocal() as db:
        try:
            # Get user from database
            user = db.query(User).filter(User.email == test_email).first()
            
            if not user:
                print(f"❌ User not found: {test_email}")
                return
            
            print(f"✅ User found:")
            print(f"  - ID: {user.id}")
            print(f"  - Email: {user.email}")
            print(f"  - Name: {user.full_name}")
            print(f"  - Role: {user.role}")
            print(f"  - Active: {user.is_active}")
            print(f"  - Verified: {user.is_verified}")
            print(f"  - Has Password Hash: {'Yes' if user.hashed_password else 'No'}")
            
            if user.hashed_password:
                # Test password verification
                password_valid = verify_password(test_password, user.hashed_password)
                print(f"  - Password '{test_password}' valid: {password_valid}")
                
                # Test with AuthService
                auth_user = AuthService.authenticate_user(db, test_email, test_password)
                print(f"  - AuthService authentication: {'Success' if auth_user else 'Failed'}")
                
                if not auth_user:
                    print("\\n🔍 Debugging AuthService failure...")
                    if not user.is_active:
                        print("  - User is not active!")
                    elif not password_valid:
                        print("  - Password verification failed!")
                    else:
                        print("  - Unknown AuthService issue")
                
                # Test different password variations
                print("\\n🔍 Testing password variations...")
                test_passwords = [
                    "Test@123",
                    "test@123", 
                    "TEST@123",
                    "Test123",
                    "test123"
                ]
                
                for pwd in test_passwords:
                    is_valid = verify_password(pwd, user.hashed_password)
                    print(f"  - '{pwd}': {is_valid}")
                    
            else:
                print("❌ No password hash found!")
                
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_authentication())