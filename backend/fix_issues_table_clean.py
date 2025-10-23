"""
Clean migration: Drop old columns and fix the issues table schema.

This script will:
1. Drop all old columns (pr_analysis_id, file_path, line_number, etc.)
2. Keep only the new schema columns (analysis_id, pattern_type, location, etc.)
3. Make analysis_id NOT NULL
4. Add proper foreign key constraint

WARNING: This will delete all existing issues data!
Run check_existing_data.py first to see what will be lost.
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def fix_issues_table():
    async with AsyncSessionLocal() as session:
        print("=" * 80)
        print("FIXING ISSUES TABLE - CLEAN MIGRATION")
        print("=" * 80)
        
        try:
            # Step 1: Check current state
            print("\n[1/6] Checking current state...")
            result = await session.execute(text("SELECT COUNT(*) FROM issues"))
            count = result.scalar()
            print(f"      Current issues count: {count}")
            
            if count > 0:
                print(f"\n⚠️  WARNING: This will delete {count} existing issues!")
                print("      Press Ctrl+C to cancel, or the script will continue in 3 seconds...")
                import time
                time.sleep(3)
            
            # Step 2: Drop foreign key constraints
            print("\n[2/6] Dropping foreign key constraints...")
            await session.execute(text("""
                ALTER TABLE issues 
                DROP CONSTRAINT IF EXISTS issues_pr_analysis_id_fkey1
            """))
            await session.execute(text("""
                ALTER TABLE issues 
                DROP CONSTRAINT IF EXISTS issues_pr_analysis_id_fkey
            """))
            await session.execute(text("""
                ALTER TABLE issues 
                DROP CONSTRAINT IF EXISTS issues_analysis_id_fkey
            """))
            print("      ✓ Constraints dropped")
            
            # Step 3: Delete all data (since we're changing schema significantly)
            print("\n[3/6] Clearing existing data...")
            await session.execute(text("DELETE FROM issues"))
            print("      ✓ Data cleared")
            
            # Step 4: Drop old columns
            print("\n[4/6] Dropping old columns...")
            old_columns = [
                'pr_analysis_id',
                'file_path', 
                'line_number',
                'message',
                'rule_id',
                'suggestion',
                'feedback',
                'issue_hash'
            ]
            for col in old_columns:
                try:
                    await session.execute(text(f"ALTER TABLE issues DROP COLUMN IF EXISTS {col}"))
                    print(f"      ✓ Dropped {col}")
                except Exception as e:
                    print(f"      ⚠️  Could not drop {col}: {e}")
            
            # Step 5: Make analysis_id NOT NULL and add foreign key
            print("\n[5/6] Fixing analysis_id column...")
            await session.execute(text("""
                ALTER TABLE issues 
                ALTER COLUMN analysis_id SET NOT NULL
            """))
            print("      ✓ Made analysis_id NOT NULL")
            
            await session.execute(text("""
                ALTER TABLE issues 
                ADD CONSTRAINT issues_analysis_id_fkey 
                FOREIGN KEY (analysis_id) REFERENCES direct_analyses(id)
                ON DELETE CASCADE
            """))
            print("      ✓ Added foreign key constraint")
            
            # Step 6: Commit changes
            print("\n[6/6] Committing changes...")
            await session.commit()
            print("      ✓ Changes committed")
            
            # Verify final state
            print("\n" + "=" * 80)
            print("VERIFICATION")
            print("=" * 80)
            
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'issues'
                ORDER BY ordinal_position
            """))
            
            print("\nFinal schema:")
            for row in result:
                nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
                print(f"  {row[0]:30} {row[1]:20} {nullable}")
            
            print("\n" + "=" * 80)
            print("✓ MIGRATION COMPLETE!")
            print("=" * 80)
            print("\nNext steps:")
            print("1. Run: python verify_database_schema.py")
            print("2. Test issue creation with your API")
            print("3. Verify feedback submission works")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(fix_issues_table())
