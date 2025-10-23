#!/usr/bin/env python3
"""
Get authentication token for demo user
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.users import User
from app.services.auth_service import AuthService
from app.core.security import get_password_hash

def get_demo_token():
    """Get authentication token for demo user"""
    db = SessionLocal()
    
    try:
        # Get demo user
        demo_user = db.query(User).filter(User.email == "demo@codenova.com").first()
        if not demo_user:
            print("❌ Demo user not found. Run create_file_batch_demo_data.py first.")
            return None
        
        # Update demo user password to a known value
        demo_password = "demo123"
        demo_user.hashed_password = get_password_hash(demo_password)
        db.commit()
        
        # Create tokens
        tokens = AuthService.create_user_tokens(db, demo_user)
        
        print("🎉 Demo user authentication token:")
        print(f"📧 Email: {demo_user.email}")
        print(f"🔑 Password: {demo_password}")
        print(f"🎫 Access Token: {tokens['access_token']}")
        print(f"🔄 Refresh Token: {tokens['refresh_token']}")
        print()
        print("You can use this token to test the API:")
        print(f'curl -X GET "http://localhost:8000/api/v1/files/" -H "Authorization: Bearer {tokens["access_token"]}"')
        print()
        print("Or login via the frontend with:")
        print(f"Email: {demo_user.email}")
        print(f"Password: {demo_password}")
        
        return tokens
        
    except Exception as e:
        print(f"❌ Error getting demo token: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    get_demo_token()