"""
Fix ALL database table issues in one go.
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def fix_all_tables():
    """Fix all database table issues."""
    
    print("=" * 80)
    print("COMPREHENSIVE DATABASE FIX")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as session:
        fixes_applied = []
        
        # FIX 1: Add missing columns to direct_analyses
        print("FIX 1: Checking direct_analyses table...")
        print("-" * 80)
        
        missing_columns = [
            ("ast_metadata", "JSON"),
            ("code_patterns", "JSON"),
            ("issue_ids", "JSON"),
            ("ast_processing_time", "FLOAT")
        ]
        
        for col_name, col_type in missing_columns:
            try:
                # Check if column exists
                result = await session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'direct_analyses' 
                    AND column_name = '{col_name}'
                """))
                exists = result.fetchone()
                
                if not exists:
                    print(f"  Adding column: {col_name}")
                    await session.execute(text(f"""
                        ALTER TABLE direct_analyses 
                        ADD COLUMN {col_name} {col_type}
                    """))
                    await session.commit()
                    fixes_applied.append(f"Added {col_name} to direct_analyses")
                    print(f"  ✓ Added {col_name}")
                else:
                    print(f"  ✓ {col_name} already exists")
            except Exception as e:
                print(f"  ⚠️  Error with {col_name}: {e}")
        
        # FIX 2: Recreate issues table with correct schema
        print("\nFIX 2: Fixing issues table...")
        print("-" * 80)
        
        try:
            # Backup old table
            print("  Backing up old issues table...")
            await session.execute(text("DROP TABLE IF EXISTS issues_old CASCADE"))
            await session.execute(text("ALTER TABLE IF EXISTS issues RENAME TO issues_old"))
            await session.commit()
            print("  ✓ Old table backed up")
            
            # Create new issues table
            print("  Creating new issues table...")
            await session.execute(text("""
                CREATE TABLE issues (
                    id VARCHAR(64) PRIMARY KEY,
                    pr_analysis_id VARCHAR(36) NOT NULL,
                    file_path VARCHAR(512) NOT NULL,
                    line_number INTEGER NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    rule_id VARCHAR(100),
                    suggestion TEXT,
                    status VARCHAR(20) DEFAULT 'open',
                    feedback TEXT,
                    issue_hash VARCHAR(64),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pr_analysis_id) REFERENCES pr_analyses(id) ON DELETE CASCADE
                )
            """))
            await session.commit()
            fixes_applied.append("Recreated issues table with correct schema")
            print("  ✓ New issues table created")
            
            # Create indexes
            print("  Creating indexes...")
            indexes = [
                "CREATE INDEX idx_issues_pr_analysis ON issues(pr_analysis_id)",
                "CREATE INDEX idx_issues_status ON issues(status)",
                "CREATE INDEX idx_issues_severity ON issues(severity)",
                "CREATE INDEX idx_issues_hash ON issues(issue_hash)"
            ]
            for idx_sql in indexes:
                await session.execute(text(idx_sql))
            await session.commit()
            print("  ✓ Indexes created")
            
        except Exception as e:
            print(f"  ❌ Error fixing issues table: {e}")
            await session.rollback()
        
        # FIX 3: Add missing columns to other tables if needed
        print("\nFIX 3: Checking other tables...")
        print("-" * 80)
        
        # Check pr_analyses for analysis_results column
        try:
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'pr_analyses' 
                AND column_name = 'analysis_results'
            """))
            if not result.fetchone():
                print("  Adding analysis_results to pr_analyses...")
                await session.execute(text("""
                    ALTER TABLE pr_analyses 
                    ADD COLUMN analysis_results JSON
                """))
                await session.commit()
                fixes_applied.append("Added analysis_results to pr_analyses")
                print("  ✓ Added analysis_results")
            else:
                print("  ✓ pr_analyses.analysis_results exists")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
        
        # Summary
        print(f"\n{'=' * 80}")
        print("FIX SUMMARY")
        print(f"{'=' * 80}\n")
        
        if fixes_applied:
            print(f"✓ Applied {len(fixes_applied)} fixes:\n")
            for i, fix in enumerate(fixes_applied, 1):
                print(f"  {i}. {fix}")
        else:
            print("✓ No fixes needed - all tables are correct!")
        
        print(f"\n{'=' * 80}")
        print("NEXT STEPS")
        print(f"{'=' * 80}\n")
        print("1. Restart your backend server (Ctrl+C then restart)")
        print("2. Try the direct code analysis again")
        print("3. Try repository analysis")
        print("4. Issues should now be created and feedback should work")
        print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(fix_all_tables())
