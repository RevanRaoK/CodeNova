#!/usr/bin/env python3
"""
Create a test admin user for API testing
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.users import User
from app.core.security import get_password_hash
from app.schemas.user import UserRole

def create_test_admin():
    """Create a test admin user"""
    db: Session = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "test@admin.com").first()
        
        if admin_user:
            print(f"Admin user already exists: {admin_user.email}")
            print(f"Role: {admin_user.role}")
            print(f"Active: {admin_user.is_active}")
            return admin_user.email, "admin123"
        
        # Create new admin user
        hashed_password = get_password_hash("admin123")
        
        admin_user = User(
            email="test@admin.com",
            full_name="Test Admin",
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Created admin user: {admin_user.email}")
        print(f"Password: admin123")
        print(f"Role: {admin_user.role}")
        
        return admin_user.email, "admin123"
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return None, None
    finally:
        db.close()

def list_all_users():
    """List all users in the database"""
    db: Session = SessionLocal()
    
    try:
        users = db.query(User).all()
        print(f"\n=== All Users in Database ({len(users)} total) ===")
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Name: {user.full_name}")
            print(f"Role: {user.role}")
            print(f"Active: {user.is_active}")
            print(f"Verified: {user.is_verified}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating test admin user...")
    list_all_users()
    email, password = create_test_admin()
    
    if email and password:
        print(f"\n✅ Test admin ready!")
        print(f"Email: {email}")
        print(f"Password: {password}")
    else:
        print("❌ Failed to create test admin")