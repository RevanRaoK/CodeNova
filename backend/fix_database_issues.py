"""
Fix common database issues.
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def fix_database_issues():
    """Fix common database issues."""
    
    print("=" * 80)
    print("DATABASE ISSUE FIXER")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as session:
        fixes_applied = []
        
        # Check and add missing columns
        print("Checking for missing columns...")
        
        # Check if issue_hash column exists
        try:
            await session.execute(text("SELECT issue_hash FROM issues LIMIT 1"))
            print("✓ issue_hash column exists")
        except Exception as e:
            print("❌ issue_hash column missing, adding...")
            try:
                await session.execute(text("""
                    ALTER TABLE issues 
                    ADD COLUMN issue_hash VARCHAR(64)
                """))
                await session.commit()
                print("✓ Added issue_hash column")
                fixes_applied.append("Added issue_hash column to issues table")
            except Exception as e2:
                print(f"❌ Failed to add issue_hash: {e2}")
        
        # Check if feedback column exists
        try:
            await session.execute(text("SELECT feedback FROM issues LIMIT 1"))
            print("✓ feedback column exists")
        except Exception as e:
            print("❌ feedback column missing, adding...")
            try:
                await session.execute(text("""
                    ALTER TABLE issues 
                    ADD COLUMN feedback TEXT
                """))
                await session.commit()
                print("✓ Added feedback column")
                fixes_applied.append("Added feedback column to issues table")
            except Exception as e2:
                print(f"❌ Failed to add feedback: {e2}")
        
        # Check if status column exists
        try:
            await session.execute(text("SELECT status FROM issues LIMIT 1"))
            print("✓ status column exists")
        except Exception as e:
            print("❌ status column missing, adding...")
            try:
                await session.execute(text("""
                    ALTER TABLE issues 
                    ADD COLUMN status VARCHAR(20) DEFAULT 'open'
                """))
                await session.commit()
                print("✓ Added status column")
                fixes_applied.append("Added status column to issues table")
            except Exception as e2:
                print(f"❌ Failed to add status: {e2}")
        
        # Update NULL status values to 'open'
        print("\nUpdating NULL status values...")
        try:
            result = await session.execute(text("""
                UPDATE issues 
                SET status = 'open' 
                WHERE status IS NULL
            """))
            await session.commit()
            if result.rowcount > 0:
                print(f"✓ Updated {result.rowcount} issues with NULL status")
                fixes_applied.append(f"Updated {result.rowcount} NULL status values")
            else:
                print("✓ No NULL status values found")
        except Exception as e:
            print(f"❌ Failed to update status: {e}")
        
        # Generate issue_hash for issues that don't have one
        print("\nGenerating missing issue_hash values...")
        try:
            result = await session.execute(text("""
                UPDATE issues 
                SET issue_hash = MD5(CONCAT(
                    COALESCE(file_path, ''),
                    COALESCE(CAST(line_number AS TEXT), ''),
                    COALESCE(message, ''),
                    COALESCE(rule_id, '')
                ))
                WHERE issue_hash IS NULL
            """))
            await session.commit()
            if result.rowcount > 0:
                print(f"✓ Generated issue_hash for {result.rowcount} issues")
                fixes_applied.append(f"Generated {result.rowcount} issue_hash values")
            else:
                print("✓ All issues have issue_hash")
        except Exception as e:
            print(f"❌ Failed to generate issue_hash: {e}")
        
        # Delete orphaned issues
        print("\nChecking for orphaned issues...")
        try:
            result = await session.execute(text("""
                DELETE FROM issues 
                WHERE pr_analysis_id NOT IN (SELECT id FROM pr_analyses)
            """))
            await session.commit()
            if result.rowcount > 0:
                print(f"✓ Deleted {result.rowcount} orphaned issues")
                fixes_applied.append(f"Deleted {result.rowcount} orphaned issues")
            else:
                print("✓ No orphaned issues found")
        except Exception as e:
            print(f"❌ Failed to delete orphaned issues: {e}")
        
        # Create indexes if missing
        print("\nCreating indexes...")
        
        indexes_to_create = [
            ("idx_issues_pr_analysis", "issues", "pr_analysis_id"),
            ("idx_issues_status", "issues", "status"),
            ("idx_issues_hash", "issues", "issue_hash"),
            ("idx_pr_analyses_repo", "pr_analyses", "repository_id"),
            ("idx_pr_analyses_status", "pr_analyses", "status"),
        ]
        
        for idx_name, table, column in indexes_to_create:
            try:
                await session.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS {idx_name} 
                    ON {table}({column})
                """))
                await session.commit()
                print(f"✓ Created/verified index {idx_name}")
            except Exception as e:
                print(f"⚠️  Index {idx_name}: {e}")
        
        # Summary
        print(f"\n\n{'=' * 80}")
        print("FIX SUMMARY")
        print(f"{'=' * 80}\n")
        
        if fixes_applied:
            print(f"Applied {len(fixes_applied)} fixes:\n")
            for i, fix in enumerate(fixes_applied, 1):
                print(f"{i}. {fix}")
        else:
            print("No fixes needed - database is healthy!")
        
        print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(fix_database_issues())
