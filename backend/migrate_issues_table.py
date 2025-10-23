"""
Migrate the issues table to the correct schema.
This will backup the old table and create a new one with the correct structure.
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def migrate_issues_table():
    """Migrate issues table to correct schema."""
    
    print("=" * 80)
    print("ISSUES TABLE MIGRATION")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Backup old issues table
            print("Step 1: Backing up old issues table...")
            await session.execute(text("""
                DROP TABLE IF EXISTS issues_old CASCADE
            """))
            await session.execute(text("""
                ALTER TABLE issues RENAME TO issues_old
            """))
            await session.commit()
            print("✓ Old table backed up as 'issues_old'")
            
            # Step 2: Create new issues table with correct schema
            print("\nStep 2: Creating new issues table with correct schema...")
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
            print("✓ New issues table created")
            
            # Step 3: Create indexes
            print("\nStep 3: Creating indexes...")
            indexes = [
                "CREATE INDEX idx_issues_pr_analysis ON issues(pr_analysis_id)",
                "CREATE INDEX idx_issues_status ON issues(status)",
                "CREATE INDEX idx_issues_severity ON issues(severity)",
                "CREATE INDEX idx_issues_hash ON issues(issue_hash)",
                "CREATE INDEX idx_issues_file_path ON issues(file_path)"
            ]
            
            for idx_sql in indexes:
                await session.execute(text(idx_sql))
            await session.commit()
            print("✓ Indexes created")
            
            # Step 4: Try to migrate data if possible
            print("\nStep 4: Checking if data can be migrated...")
            result = await session.execute(text("SELECT COUNT(*) FROM issues_old"))
            old_count = result.scalar()
            
            if old_count > 0:
                print(f"  Found {old_count} records in old table")
                print("  ⚠️  Cannot auto-migrate due to schema differences")
                print("  Old data is preserved in 'issues_old' table")
            else:
                print("  No data in old table to migrate")
            
            # Step 5: Verify new table
            print("\nStep 5: Verifying new table...")
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'issues'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print("  New table columns:")
            for col_name, col_type, nullable in columns:
                null_str = "NULL" if nullable == 'YES' else "NOT NULL"
                print(f"    - {col_name:30} {col_type:20} {null_str}")
            
            print(f"\n{'=' * 80}")
            print("✓ MIGRATION COMPLETE")
            print(f"{'=' * 80}")
            print()
            print("Next steps:")
            print("1. Restart your backend server")
            print("2. Trigger a new repository analysis")
            print("3. Issues will now be created with the correct schema")
            print("4. Feedback functionality should work")
            print()
            print("Note: Old data is in 'issues_old' table if you need it")
            print(f"{'=' * 80}\n")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will recreate the issues table!")
    print("Old data will be backed up to 'issues_old'")
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() == 'yes':
        asyncio.run(migrate_issues_table())
    else:
        print("Migration cancelled")
