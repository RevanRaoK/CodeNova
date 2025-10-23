"""
Complete database reset - drops all tables and recreates from models.
USE ONLY IN DEVELOPMENT!
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, engine, Base

# Import all models to ensure they're registered with Base
from app.models.users import User
from app.models.team import Team
from app.models.feedback import Issue, FeedbackRecord, ModelVersion
from app.models.github_integration import GitHubRepository, PRAnalysis
from app.models.analysis import DirectAnalysis

async def reset_database():
    print("=" * 80)
    print("DATABASE RESET - DROPPING ALL TABLES")
    print("=" * 80)
    
    async with AsyncSessionLocal() as session:
        # Drop all tables
        print("\n1. Dropping all existing tables...")
        await session.execute(text("DROP SCHEMA public CASCADE"))
        await session.execute(text("CREATE SCHEMA public"))
        await session.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        await session.execute(text("GRANT ALL ON SCHEMA public TO public"))
        await session.commit()
        print("   ✓ All tables dropped")
    
    # Recreate all tables from models
    print("\n2. Creating all tables from models...")
    async with AsyncSessionLocal() as session:
        def create_tables(sync_conn):
            Base.metadata.create_all(bind=sync_conn)
        
        connection = await session.connection()
        await connection.run_sync(create_tables)
        await session.commit()
    print("   ✓ All tables created")
    
    # Verify tables were created
    print("\n3. Verifying tables...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print(f"   ✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"     - {table}")
    
    print("\n" + "=" * 80)
    print("DATABASE RESET COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(reset_database())
