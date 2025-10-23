#!/usr/bin/env python3
"""
Simple admin user creation script
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment to development if not set
os.environ.setdefault('ENVIRONMENT', 'development')

def create_admin():
    try:
        from app.core.database import SessionLocal
        from app.models.users import User, UserRole
        from app.core.security import get_password_hash
        
        db = SessionLocal()
        
        # Admin credentials
        admin_email = "revankokkirala@gmail.com"
        admin_password = "Test@123"
        admin_name = "Revan Kokkirala"
        
        print("Creating admin user...")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == admin_email).first()
        if existing_user:
            print(f"User already exists: {existing_user.email}")
            if existing_user.role != UserRole.ADMIN:
                existing_user.role = UserRole.ADMIN
                db.commit()
                print("Updated user role to ADMIN")
            return existing_user
        
        # Create new admin user
        hashed_password = get_password_hash(admin_password)
        
        admin_user = User(
            email=admin_email,
            full_name=admin_name,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Name: {admin_user.full_name}")
        print(f"   Role: {admin_user.role}")
        print(f"   ID: {admin_user.id}")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()