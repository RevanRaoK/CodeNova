#!/usr/bin/env python3
"""
Update user role to admin
Usage: python update_user_role.py
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
    
    print("🔧 Updating user role to admin...")
    print("=================================")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        # Update user role
        result = db.execute(text("""
            UPDATE users 
            SET role = 'ADMIN', updated_at = NOW()
            WHERE email = :email
            RETURNING id, email, full_name, role, is_active
        """), {"email": "rachapranavanadh@gmail.com"})
        
        updated_user = result.fetchone()
        db.commit()
        
        if updated_user:
            print("✅ User role updated successfully!")
            print(f"  - ID: {updated_user.id}")
            print(f"  - Email: {updated_user.email}")
            print(f"  - Name: {updated_user.full_name}")
            print(f"  - Role: {updated_user.role}")
            print(f"  - Active: {updated_user.is_active}")
        else:
            print("❌ User not found or update failed")
    
    print("\n🎉 User is now an admin!")
    print("You can login at: http://localhost:5173/admin/login")
    # print("Credentials: revankokkirala@gmail.com / Test@123")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()