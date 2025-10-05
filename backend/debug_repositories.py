#!/usr/bin/env python3
"""
Debug script to test the repositories endpoint issue
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.github_integration import GitHubRepository


async def test_repositories_query():
    """Test the repositories query that's causing issues"""
    try:
        async with AsyncSessionLocal() as db:
            print("Testing repositories query...")
            
            # Test the query that's failing
            query = select(GitHubRepository).limit(10)
            
            print("Executing query...")
            result = await db.execute(query)
            
            print("Getting scalars...")
            repositories = result.scalars().all()
            
            print(f"Found {len(repositories)} repositories")
            
            # Test count query
            count_query = select(func.count(GitHubRepository.id))
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            print(f"Total count: {total}")
            
            return repositories, total
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    asyncio.run(test_repositories_query())