"""
Simple database check using direct SQL queries.
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def simple_db_check():
    """Simple database check."""
    
    print("=" * 80)
    print("SIMPLE DATABASE CHECK")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as session:
        # Get all tables
        result = await session.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        tables = [row[0] for row in result.fetchall()]
        
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        print()
        
        # Check each important table
        important_tables = ['users', 'teams', 'github_repositories', 'pr_analyses', 'issues']
        
        for table in important_tables:
            print(f"\nChecking table: {table}")
            print("-" * 80)
            
            if table not in tables:
                print(f"❌ Table '{table}' does NOT exist!")
                continue
            
            # Get columns
            result = await session.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print(f"✓ Table exists with {len(columns)} columns:")
            for col_name, col_type, nullable in columns:
                null_str = "NULL" if nullable == 'YES' else "NOT NULL"
                print(f"  - {col_name:30} {col_type:20} {null_str}")
            
            # Get row count
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"\n  Total records: {count}")
        
        # Check issues table specifically
        print(f"\n\n{'=' * 80}")
        print("ISSUES TABLE DETAILED CHECK")
        print(f"{'=' * 80}\n")
        
        if 'issues' in tables:
            # Check for required columns
            required_cols = ['id', 'pr_analysis_id', 'file_path', 'line_number', 
                           'severity', 'message', 'status', 'feedback', 'issue_hash']
            
            result = await session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'issues'
            """))
            existing_cols = [row[0] for row in result.fetchall()]
            
            print("Required columns check:")
            for col in required_cols:
                if col in existing_cols:
                    print(f"  ✓ {col}")
                else:
                    print(f"  ❌ MISSING: {col}")
            
            # Check for orphaned issues
            result = await session.execute(text("""
                SELECT COUNT(*) 
                FROM issues i
                LEFT JOIN pr_analyses pa ON i.pr_analysis_id = pa.id
                WHERE pa.id IS NULL
            """))
            orphaned = result.scalar()
            
            if orphaned > 0:
                print(f"\n  ⚠️  Found {orphaned} orphaned issues")
            else:
                print(f"\n  ✓ No orphaned issues")
            
            # Show sample issues
            result = await session.execute(text("""
                SELECT id, pr_analysis_id, file_path, severity, status
                FROM issues
                ORDER BY created_at DESC
                LIMIT 5
            """))
            sample_issues = result.fetchall()
            
            if sample_issues:
                print(f"\n  Recent issues (last 5):")
                for issue_id, pr_id, file_path, severity, status in sample_issues:
                    print(f"    - ID: {issue_id[:8]}... | PR: {pr_id[:8]}... | {file_path} | {severity} | {status}")
            else:
                print(f"\n  No issues found in database")
        
        # Check pr_analyses
        print(f"\n\n{'=' * 80}")
        print("PR_ANALYSES TABLE CHECK")
        print(f"{'=' * 80}\n")
        
        if 'pr_analyses' in tables:
            result = await session.execute(text("""
                SELECT id, repository_id, status, issues_found
                FROM pr_analyses
                ORDER BY created_at DESC
                LIMIT 5
            """))
            analyses = result.fetchall()
            
            if analyses:
                print("Recent analyses (last 5):")
                for analysis_id, repo_id, status, issues_found in analyses:
                    # Count actual issues
                    result2 = await session.execute(text(f"""
                        SELECT COUNT(*) FROM issues WHERE pr_analysis_id = '{analysis_id}'
                    """))
                    actual_issues = result2.scalar()
                    
                    match = "✓" if issues_found == actual_issues else "⚠️ MISMATCH"
                    print(f"  - ID: {analysis_id[:8]}... | Status: {status} | Issues: {issues_found} | Actual: {actual_issues} {match}")
            else:
                print("No analyses found")
        
        print(f"\n{'=' * 80}")
        print("CHECK COMPLETE")
        print(f"{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(simple_db_check())
