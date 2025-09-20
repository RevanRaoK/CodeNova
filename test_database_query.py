#!/usr/bin/env python3
"""
Test the database query directly
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_database_query():
    print("Testing database query...")
    
    try:
        from app.core.database import SessionLocal
        from app.models.analysis import DirectAnalysis
        from app.models.users import User
        
        db = SessionLocal()
        
        try:
            # Test if we can query the DirectAnalysis table
            print("1. Testing DirectAnalysis table query...")
            count = db.query(DirectAnalysis).count()
            print(f"✅ DirectAnalysis table exists with {count} records")
            
            # Test if we can query users
            print("2. Testing User table query...")
            user_count = db.query(User).count()
            print(f"✅ User table exists with {user_count} users")
            
            # Test if we can find a specific user
            print("3. Testing specific user query...")
            user = db.query(User).filter(User.email == "demo@example.com").first()
            if user:
                print(f"✅ Found user: {user.email} (ID: {user.id})")
                
                # Test querying analyses for this user
                print("4. Testing user's analyses...")
                user_analyses = db.query(DirectAnalysis).filter(DirectAnalysis.user_id == user.id).all()
                print(f"✅ User has {len(user_analyses)} analyses")
                
                for analysis in user_analyses:
                    print(f"  - Analysis {analysis.id}: {analysis.language} ({analysis.status})")
                    
            else:
                print("❌ User demo@example.com not found")
                
                # List all users
                all_users = db.query(User).all()
                print(f"Available users:")
                for u in all_users:
                    print(f"  - {u.email} (ID: {u.id})")
            
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Database query failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database_query()