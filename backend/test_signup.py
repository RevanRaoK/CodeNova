#!/usr/bin/env python3
"""
Test script to debug signup issues
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import SessionLocal
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate

def test_signup():
    """Test the signup process."""
    db = SessionLocal()
    
    try:
        # Create test user data
        user_data = UserCreate(
            email="test@example.com",
            full_name="Test User",
            password="TestPass123!"
        )
        
        print("Creating user...")
        user = AuthService.create_user(db, user_data)
        print(f"User created successfully: {user.id}, {user.email}, {user.full_name}")
        
        print("Creating tokens...")
        tokens = AuthService.create_user_tokens(db, user)
        print(f"Tokens created successfully: {tokens['token_type']}")
        
        print("✅ Signup test successful!")
        
    except Exception as e:
        print(f"❌ Signup test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_signup()