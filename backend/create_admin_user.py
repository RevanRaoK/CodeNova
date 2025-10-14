#!/usr/bin/env python3
"""
Create admin user for CodeNova
Usage: python create_admin_user.py
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment to development if not set
os.environ.setdefault('ENVIRONMENT', 'development')

try:
    from app.core.database import SessionLocal
    from app.services.auth_service import AuthService
    from app.schemas.user import UserCreate
    from app.models.users import User
    from sqlalchemy.orm import Session

    def create_admin_user():
        """Create admin user with specified credentials."""
        db = SessionLocal()
        
        try:
            # Admin credentials
            admin_email = "revankokkirala@gmail.com"
            admin_password = "Test@123"
            admin_name = "Revan Kokkirala"
            
            print("🔧 Creating Admin User")
            print("=" * 30)
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == admin_email).first()
            if existing_user:
                print(f"✅ User already exists!")
                print(f"   Email: {existing_user.email}")
                print(f"   Name: {existing_user.full_name}")
                print(f"   Role: {existing_user.role}")
                print(f"   ID: {existing_user.id}")
                
                # Update to admin role if not already
                if existing_user.role != 'ADMIN':
                    existing_user.role = 'ADMIN'
                    db.commit()
                    print("✅ Updated user role to ADMIN!")
                
                return existing_user
            
            # Create admin user data
            user_data = UserCreate(
                email=admin_email,
                full_name=admin_name,
                password=admin_password
            )
            
            print(f"Creating admin user: {admin_email}")
            user = AuthService.create_user(db, user_data)
            
            # Set role to ADMIN
            user.role = 'ADMIN'
            db.commit()
            
            print(f"✅ Admin user created successfully!")
            print(f"   Email: {user.email}")
            print(f"   Name: {user.full_name}")
            print(f"   Role: {user.role}")
            print(f"   ID: {user.id}")
            print(f"   Active: {user.is_active}")
            
            return user
            
        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            db.close()

    def test_admin_login():
        """Test login with the admin user."""
        db = SessionLocal()
        
        try:
            print("\n🔐 Testing Admin Login")
            print("=" * 25)
            
            user = AuthService.authenticate_user(db, "revankokkirala@gmail.com", "Test@123")
            
            if user:
                print("✅ Admin login test successful!")
                print(f"   Authenticated user: {user.email}")
                print(f"   Role: {user.role}")
                
                # Test token creation
                tokens = AuthService.create_user_tokens(db, user)
                print("✅ Token creation successful!")
                print(f"   Token type: {tokens['token_type']}")
                
            else:
                print("❌ Admin login test failed - authentication returned None")
                
        except Exception as e:
            print(f"❌ Admin login test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

    if __name__ == "__main__":
        print("CodeNova Admin User Setup")
        print("=" * 40)
        
        # Create admin user
        user = create_admin_user()
        
        if user:
            # Test login
            test_admin_login()
            
            print("\n" + "=" * 60)
            print("🎉 Admin setup complete! You can now login with:")
            print("   Email: revankokkirala@gmail.com")
            print("   Password: Test@123")
            print("   Role: ADMIN")
            print("   Frontend URL: http://localhost:5173")
            print("   Admin Panel: http://localhost:5173/admin")
            print("=" * 60)
        else:
            print("\n❌ Admin setup failed. Please check the error messages above.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory and all dependencies are installed.")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()