#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.users import User
from app.services.auth_service import AuthService

def get_user2_token():
    """Get authentication token for user 2"""
    db = SessionLocal()
    
    try:
        # Find user with ID 2
        user = db.query(User).filter(User.id == 2).first()
        
        if not user:
            print("❌ User with ID 2 not found.")
            return None
            
        print(f"✅ Found user: {user.email}")
        
        # Generate token
        auth_service = AuthService()
        tokens = auth_service.create_user_tokens(db, user)
        token_data = tokens["access_token"]
        
        print(f"✅ Token generated successfully")
        print(f"Token: {token_data}")
        
        return token_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("Getting token for user 2...")
    print("=" * 40)
    get_user2_token()