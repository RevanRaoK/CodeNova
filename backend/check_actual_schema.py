"""Check the actual database schema to understand the issue."""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check_schema():
    async with AsyncSessionLocal() as session:
        # Check issues table structure
        result = await session.execute(text('''
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'issues'
            ORDER BY ordinal_position
        '''))
        print('=== ISSUES TABLE COLUMNS ===')
        for row in result:
            print(f'{row[0]:30} {row[1]:20} NULL={row[2]:5} DEFAULT={row[3]}')
        
        # Check if pr_analysis_id exists
        result = await session.execute(text('''
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_name = 'issues' AND column_name = 'pr_analysis_id'
        '''))
        pr_col = result.fetchone()
        print(f'\npr_analysis_id exists: {pr_col is not None}')
        
        # Check if analysis_id exists
        result = await session.execute(text('''
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_name = 'issues' AND column_name = 'analysis_id'
        '''))
        analysis_col = result.fetchone()
        print(f'analysis_id exists: {analysis_col is not None}')
        
        # Check foreign keys
        result = await session.execute(text('''
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'issues'
        '''))
        print('\n=== FOREIGN KEYS ===')
        for row in result:
            print(f'{row[0]}: {row[1]} -> {row[2]}.{row[3]}')

if __name__ == "__main__":
    asyncio.run(check_schema())
