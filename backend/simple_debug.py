#!/usr/bin/env python3
"""
Simple SQL debug script to check user data
Usage: python simple_debug.py
"""

import os
import psycopg2
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def debug_user():
    print("🔍 Simple user debug...")
    print("======================")
    
    # Database connection (using actual config credentials)
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="codenova_db",
            user="postgres",
            password="codenova_secure_password"
        )
        cursor = conn.cursor()
        print("✅ Connected to database")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure PostgreSQL is running and credentials are correct")
        return
    
    # Check user
    test_email = "revankokkirala@gmail.com"
    test_password = "Test@123"
    
    try:
        cursor.execute("""
            SELECT id, email, full_name, role, is_active, is_verified, hashed_password, created_at
            FROM users 
            WHERE email = %s
        """, (test_email,))
        
        user = cursor.fetchone()
        
        if user:
            user_id, email, full_name, role, is_active, is_verified, hashed_password, created_at = user
            
            print(f"✅ User found:")
            print(f"  - ID: {user_id}")
            print(f"  - Email: {email}")
            print(f"  - Name: {full_name}")
            print(f"  - Role: {role}")
            print(f"  - Active: {is_active}")
            print(f"  - Verified: {is_verified}")
            print(f"  - Created: {created_at}")
            print(f"  - Has Password Hash: {'Yes' if hashed_password else 'No'}")
            
            if hashed_password:
                # Test password
                try:
                    password_valid = verify_password(test_password, hashed_password)
                    print(f"  - Password '{test_password}' valid: {password_valid}")
                    
                    if not password_valid:
                        print("\\n🔍 Testing other password variations...")
                        test_passwords = ["test@123", "TEST@123", "Test123", "test123"]
                        for pwd in test_passwords:
                            is_valid = verify_password(pwd, hashed_password)
                            print(f"    - '{pwd}': {is_valid}")
                            
                except Exception as e:
                    print(f"  - Password verification error: {e}")
                    
                # Check if user should be able to login
                if is_active and password_valid:
                    print("\\n✅ User should be able to login!")
                elif not is_active:
                    print("\\n❌ User is not active - this prevents login")
                elif not password_valid:
                    print("\\n❌ Password is invalid - this prevents login")
                    
            else:
                print("\\n❌ No password hash - user cannot login")
                
        else:
            print(f"❌ User not found: {test_email}")
            
            # Check if any users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            print(f"Total users in database: {count}")
            
            if count > 0:
                cursor.execute("SELECT email, role FROM users LIMIT 5")
                users = cursor.fetchall()
                print("Sample users:")
                for email, role in users:
                    print(f"  - {email} ({role})")
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    debug_user()