"""Check what data exists in the issues table."""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check_data():
    async with AsyncSessionLocal() as session:
        print("=" * 80)
        print("CHECKING EXISTING DATA IN ISSUES TABLE")
        print("=" * 80)
        
        # Total count
        result = await session.execute(text("SELECT COUNT(*) FROM issues"))
        total = result.scalar()
        print(f"\nTotal issues: {total}")
        
        # Count by pr_analysis_id
        result = await session.execute(text("""
            SELECT COUNT(*) FROM issues 
            WHERE pr_analysis_id IS NOT NULL
        """))
        pr_count = result.scalar()
        print(f"Issues with pr_analysis_id: {pr_count}")
        
        # Count by analysis_id
        result = await session.execute(text("""
            SELECT COUNT(*) FROM issues 
            WHERE analysis_id IS NOT NULL
        """))
        analysis_count = result.scalar()
        print(f"Issues with analysis_id: {analysis_count}")
        
        # Check pr_analyses table
        result = await session.execute(text("SELECT COUNT(*) FROM pr_analyses"))
        pr_analyses_count = result.scalar()
        print(f"\nTotal pr_analyses records: {pr_analyses_count}")
        
        # Check direct_analyses table
        try:
            result = await session.execute(text("SELECT COUNT(*) FROM direct_analyses"))
            direct_analyses_count = result.scalar()
            print(f"Total direct_analyses records: {direct_analyses_count}")
        except Exception as e:
            print(f"direct_analyses table doesn't exist or error: {e}")
        
        # Sample some data
        if total > 0:
            print("\n" + "=" * 80)
            print("SAMPLE DATA (first 3 records)")
            print("=" * 80)
            result = await session.execute(text("""
                SELECT 
                    id,
                    pr_analysis_id,
                    analysis_id,
                    COALESCE(file_path, 'N/A') as file_path,
                    COALESCE(pattern_type, 'N/A') as pattern_type,
                    severity,
                    created_at
                FROM issues
                LIMIT 3
            """))
            for row in result:
                print(f"\nID: {row[0][:20]}...")
                print(f"  pr_analysis_id: {row[1]}")
                print(f"  analysis_id: {row[2]}")
                print(f"  file_path: {row[3]}")
                print(f"  pattern_type: {row[4]}")
                print(f"  severity: {row[5]}")
                print(f"  created_at: {row[6]}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        
        if total == 0:
            print("\n✓ No data in issues table - safe to do clean migration")
        elif pr_count > 0 and analysis_count == 0:
            print(f"\n⚠️  {pr_count} issues exist with OLD schema (pr_analysis_id)")
            print("   Options:")
            print("   1. Delete all and start fresh (RECOMMENDED if test data)")
            print("   2. Migrate data to new schema (complex)")
        elif analysis_count > 0 and pr_count == 0:
            print(f"\n⚠️  {analysis_count} issues exist with NEW schema (analysis_id)")
            print("   Just need to drop old columns")
        else:
            print(f"\n⚠️  Mixed data: {pr_count} old + {analysis_count} new")
            print("   Need to decide which to keep")

if __name__ == "__main__":
    asyncio.run(check_data())
