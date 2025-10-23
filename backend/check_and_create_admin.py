#!/usr/bin/env python3
"""
Check if admin user exists and create one if needed.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.users import User, UserRole
from app.core.security import get_password_hash
from datetime import datetime

def main():
    """Check for admin user and create if needed."""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check for existing admin users
        admin_users = db.query(User).filter(User.role == UserRole.ADMIN).all()
        
        print("=" * 60)
        print("Admin User Check")
        print("=" * 60)
        
        if admin_users:
            print(f"\n✓ Found {len(admin_users)} admin user(s):\n")
            for user in admin_users:
                print(f"  ID: {user.id}")
                print(f"  Email: {user.email}")
                print(f"  Name: {user.full_name or 'N/A'}")
                print(f"  Active: {user.is_active}")
                print(f"  Created: {user.created_at}")
                print()
        else:
            print("\n✗ No admin users found!")
            print("\nWould you like to create an admin user? (y/n): ", end='')
            response = input().strip().lower()
            
            if response == 'y':
                print("\nCreating admin user...")
                print("Email: ", end='')
                email = input().strip()
                
                print("Password: ", end='')
                password = input().strip()
                
                print("Full Name (optional): ", end='')
                full_name = input().strip() or None
                
                # Check if user already exists
                existing_user = db.query(User).filter(User.email == email).first()
                
                if existing_user:
                    print(f"\n✗ User with email {email} already exists!")
                    print(f"  Current role: {existing_user.role.value}")
                    print("\nWould you like to upgrade this user to admin? (y/n): ", end='')
                    upgrade = input().strip().lower()
                    
                    if upgrade == 'y':
                        existing_user.role = UserRole.ADMIN
                        existing_user.is_active = True
                        db.commit()
                        print(f"\n✓ User {email} upgraded to admin!")
                    else:
                        print("\nNo changes made.")
                else:
                    # Create new admin user
                    new_admin = User(
                        email=email,
                        hashed_password=get_password_hash(password),
                        full_name=full_name,
                        role=UserRole.ADMIN,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.add(new_admin)
                    db.commit()
                    db.refresh(new_admin)
                    
                    print(f"\n✓ Admin user created successfully!")
                    print(f"  ID: {new_admin.id}")
                    print(f"  Email: {new_admin.email}")
                    print(f"  Role: {new_admin.role.value}")
            else:
                print("\nNo admin user created.")
        
        # Show all users
        print("\n" + "=" * 60)
        print("All Users Summary")
        print("=" * 60)
        
        all_users = db.query(User).all()
        print(f"\nTotal users: {len(all_users)}\n")
        
        role_counts = {}
        for user in all_users:
            role = user.role.value
            role_counts[role] = role_counts.get(role, 0) + 1
        
        print("Users by role:")
        for role, count in sorted(role_counts.items()):
            print(f"  {role}: {count}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
