#!/usr/bin/env python3
"""
Setup script to create a test user for development
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import SessionLocal, engine
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.models.users import User
from sqlalchemy.orm import Session

def create_test_user():
    """Create a test user for development."""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            print("✅ Test user already exists!")
            print(f"   Email: {existing_user.email}")
            print(f"   Name: {existing_user.full_name}")
            print(f"   ID: {existing_user.id}")
            return existing_user
        
        # Create test user data
        user_data = UserCreate(
            email="test@example.com",
            full_name="Test User",
            password="TestPass123!"
        )
        
        print("Creating test user...")
        user = AuthService.create_user(db, user_data)
        print(f"✅ User created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.full_name}")
        print(f"   ID: {user.id}")
        print(f"   Password: TestPass123!")
        
        return user
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def test_login():
    """Test login with the created user."""
    db = SessionLocal()
    
    try:
        print("\nTesting login...")
        user = AuthService.authenticate_user(db, "test@example.com", "TestPass123!")
        
        if user:
            print("✅ Login test successful!")
            print(f"   Authenticated user: {user.email}")
            
            # Test token creation
            tokens = AuthService.create_user_tokens(db, user)
            print("✅ Token creation successful!")
            print(f"   Token type: {tokens['token_type']}")
            
        else:
            print("❌ Login test failed - authentication returned None")
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("CodeNova Test User Setup")
    print("=" * 30)
    
    # Create test user
    user = create_test_user()
    
    if user:
        # Test login
        test_login()
        
        print("\n" + "=" * 50)
        print("🎉 Setup complete! You can now use these credentials:")
        print("   Email: test@example.com")
        print("   Password: TestPass123!")
        print("=" * 50)
    else:
        print("\n❌ Setup failed. Please check the error messages above.")