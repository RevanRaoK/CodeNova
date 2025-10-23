"""
Interactive fix script - guides you through fixing the issues table.

Run this and follow the prompts.
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    print("=" * 80)
    print("ISSUES TABLE FIX - INTERACTIVE GUIDE")
    print("=" * 80)
    
    async with AsyncSessionLocal() as session:
        # Step 1: Diagnose
        print("\n[STEP 1] Diagnosing the problem...")
        
        result = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_name = 'issues' AND column_name = 'pr_analysis_id'
        """))
        has_pr_col = result.fetchone() is not None
        
        result = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_name = 'issues' AND column_name = 'analysis_id'
        """))
        has_analysis_col = result.fetchone() is not None
        
        result = await session.execute(text("SELECT COUNT(*) FROM issues"))
        count = result.scalar()
        
        print(f"\n  Has pr_analysis_id column: {has_pr_col}")
        print(f"  Has analysis_id column: {has_analysis_col}")
        print(f"  Current issues count: {count}")
        
        if has_pr_col and has_analysis_col:
            print("\n  ❌ PROBLEM CONFIRMED: Table has BOTH old and new columns!")
        elif has_pr_col and not has_analysis_col:
            print("\n  ⚠️  Table has only OLD schema")
        elif not has_pr_col and has_analysis_col:
            print("\n  ✓ Table has correct NEW schema (might just need constraint fix)")
        else:
            print("\n  ❓ Unexpected state")
        
        # Step 2: Recommend solution
        print("\n" + "=" * 80)
        print("[STEP 2] Recommended Solution")
        print("=" * 80)
        
        if count == 0:
            print("\n✓ Good news: No data to lose!")
            print("\nRECOMMENDATION: Use the NUCLEAR OPTION (fastest)")
            print("  → python reset_issues_table.py")
            print("\nThis will:")
            print("  1. Drop the issues table")
            print("  2. Recreate it from your model")
            print("  3. Done in 2 seconds")
        else:
            print(f"\n⚠️  You have {count} issues in the table")
            print("\nOPTION 1: Clean Migration (keeps table, drops columns)")
            print("  → python fix_issues_table_clean.py")
            print("  Pros: More controlled")
            print("  Cons: Deletes data anyway since schemas incompatible")
            print("\nOPTION 2: Nuclear Option (drop and recreate)")
            print("  → python reset_issues_table.py")
            print("  Pros: Fastest, cleanest")
            print("  Cons: Deletes everything")
            print("\nSince the data can't be migrated (incompatible schemas),")
            print("both options will delete it. Nuclear option is simpler.")
        
        # Step 3: Show what to run
        print("\n" + "=" * 80)
        print("[STEP 3] What To Do Next")
        print("=" * 80)
        
        print("\n1. Run ONE of these:")
        print("   → python reset_issues_table.py          (RECOMMENDED)")
        print("   → python fix_issues_table_clean.py      (alternative)")
        
        print("\n2. Verify it worked:")
        print("   → python verify_database_schema.py")
        
        print("\n3. Test your API:")
        print("   - Upload a file for analysis")
        print("   - Check if issues are created")
        print("   - Try submitting feedback")
        
        print("\n" + "=" * 80)
        print("Ready to fix? Run one of the scripts above!")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
