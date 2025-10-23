"""
Nuclear option: Drop and recreate the issues table from scratch.

This is the simplest fix if you don't care about existing data.
It will drop the table and let SQLAlchemy recreate it with the correct schema.
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, engine
from app.models.feedback import Issue

async def reset_issues_table():
    print("=" * 80)
    print("RESETTING ISSUES TABLE (NUCLEAR OPTION)")
    print("=" * 80)
    
    async with AsyncSessionLocal() as session:
        try:
            # Check current count
            result = await session.execute(text("SELECT COUNT(*) FROM issues"))
            count = result.scalar()
            print(f"\nCurrent issues count: {count}")
            
            if count > 0:
                print(f"\n⚠️  WARNING: This will delete {count} existing issues!")
                print("Press Ctrl+C to cancel, or the script will continue in 3 seconds...")
                import time
                time.sleep(3)
            
            print("\n[1/3] Dropping issues table...")
            await session.execute(text("DROP TABLE IF EXISTS issues CASCADE"))
            await session.commit()
            print("      ✓ Table dropped")
            
            print("\n[2/3] Recreating issues table from model...")
            # Import Base to get all models
            from app.core.database import Base
            
            # Create just the issues table
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all, tables=[Issue.__table__])
            
            print("      ✓ Table recreated")
            
            print("\n[3/3] Verifying new schema...")
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'issues'
                ORDER BY ordinal_position
            """))
            
            print("\nNew schema:")
            for row in result:
                nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
                print(f"  {row[0]:30} {row[1]:20} {nullable}")
            
            print("\n" + "=" * 80)
            print("✓ RESET COMPLETE!")
            print("=" * 80)
            print("\nThe issues table now matches your model exactly.")
            print("Test by uploading a file for analysis.")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(reset_issues_table())
