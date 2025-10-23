#!/usr/bin/env python3
"""
Cleanup duplicate GitHub OAuth integrations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def cleanup_duplicates():
    """Remove duplicate GitHub OAuth integrations, keeping only the most recent one per user"""
    
    try:
        with engine.connect() as connection:
            print("Cleaning up duplicate GitHub OAuth integrations...")
            print("=" * 60)
            
            # First, check for duplicates
            check_query = text("""
                SELECT user_id, github_user_id, COUNT(*) as count
                FROM github_oauth_integrations
                GROUP BY user_id, github_user_id
                HAVING COUNT(*) > 1;
            """)
            
            result = connection.execute(check_query)
            duplicates = result.fetchall()
            
            if not duplicates:
                print("✅ No duplicate integrations found!")
                return True
            
            print(f"Found {len(duplicates)} sets of duplicate integrations:")
            for dup in duplicates:
                print(f"  User ID: {dup[0]}, GitHub User ID: {dup[1]}, Count: {dup[2]}")
            
            print("\nRemoving duplicates (keeping most recent)...")
            
            # Delete duplicates, keeping only the most recent one for each user
            cleanup_query = text("""
                DELETE FROM github_oauth_integrations
                WHERE id IN (
                    SELECT id
                    FROM (
                        SELECT id,
                               ROW_NUMBER() OVER (
                                   PARTITION BY user_id, github_user_id 
                                   ORDER BY updated_at DESC, created_at DESC
                               ) as rn
                        FROM github_oauth_integrations
                    ) t
                    WHERE t.rn > 1
                );
            """)
            
            result = connection.execute(cleanup_query)
            connection.commit()
            
            deleted_count = result.rowcount
            print(f"✅ Deleted {deleted_count} duplicate integration(s)")
            
            # Verify cleanup
            result = connection.execute(check_query)
            remaining_duplicates = result.fetchall()
            
            if remaining_duplicates:
                print(f"⚠️  Warning: {len(remaining_duplicates)} duplicate(s) still remain")
                return False
            else:
                print("✅ All duplicates cleaned up successfully!")
                return True
        
    except Exception as e:
        print(f"❌ Error cleaning up duplicates: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_current_integrations():
    """Show current GitHub OAuth integrations"""
    
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT id, user_id, github_user_id, github_username, 
                       is_active, created_at, updated_at
                FROM github_oauth_integrations
                ORDER BY user_id, created_at DESC;
            """)
            
            result = connection.execute(query)
            integrations = result.fetchall()
            
            print("\n" + "=" * 60)
            print("Current GitHub OAuth Integrations:")
            print("=" * 60)
            
            if not integrations:
                print("No integrations found.")
            else:
                for integration in integrations:
                    print(f"ID: {integration[0]}")
                    print(f"  User ID: {integration[1]}")
                    print(f"  GitHub User ID: {integration[2]}")
                    print(f"  GitHub Username: {integration[3]}")
                    print(f"  Active: {integration[4]}")
                    print(f"  Created: {integration[5]}")
                    print(f"  Updated: {integration[6]}")
                    print("-" * 60)
            
            print(f"Total: {len(integrations)} integration(s)")
            
    except Exception as e:
        print(f"❌ Error showing integrations: {e}")

if __name__ == "__main__":
    print("CodeNova - GitHub OAuth Integration Cleanup")
    print("=" * 60)
    
    # Show current state
    show_current_integrations()
    
    # Cleanup duplicates
    success = cleanup_duplicates()
    
    if success:
        # Show final state
        show_current_integrations()
        print("\n" + "=" * 60)
        print("✅ Cleanup completed successfully!")
        print("You can now try connecting to GitHub again.")
        print("=" * 60)
    else:
        print("\n❌ Cleanup failed. Please check the error messages above.")
        sys.exit(1)
