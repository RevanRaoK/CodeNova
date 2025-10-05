#!/usr/bin/env python3
"""
Script to create test GitHub repository data
"""

import asyncio
import sys
import os
from datetime import datetime
import uuid

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.github_integration import GitHubRepository
from app.models.users import User


async def create_test_repository():
    """Create a test GitHub repository"""
    try:
        async with AsyncSessionLocal() as db:
            print("Creating test repository...")
            
            # First, let's check if we have any users
            user_query = select(User).limit(5)
            user_result = await db.execute(user_query)
            users = user_result.scalars().all()
            
            print(f"Found {len(users)} users:")
            for user in users:
                print(f"  - {user.email} (ID: {user.id}, Role: {user.role})")
            
            if not users:
                print("No users found. Cannot create repository without a user.")
                return
            
            # Use the first user (preferably admin)
            admin_user = None
            for user in users:
                if user.role == "ADMIN":
                    admin_user = user
                    break
            
            if not admin_user:
                admin_user = users[0]  # Use first user if no admin found
            
            print(f"Using user: {admin_user.email}")
            
            # Create test repository
            test_repo = GitHubRepository(
                id=str(uuid.uuid4()),
                user_id=admin_user.id,
                repo_name="testuser/test-repo",
                repo_url="https://github.com/testuser/test-repo",
                webhook_id="webhook_123",
                webhook_secret="secret_123",
                access_token="token_123",
                is_active=True,
                default_branch="main",
                repository_settings={},
                permissions={}
            )
            
            db.add(test_repo)
            await db.commit()
            
            print(f"Created test repository: {test_repo.repo_name}")
            print(f"Repository ID: {test_repo.id}")
            
            # Verify it was created
            verify_query = select(GitHubRepository)
            verify_result = await db.execute(verify_query)
            all_repos = verify_result.scalars().all()
            
            print(f"Total repositories in database: {len(all_repos)}")
            for repo in all_repos:
                print(f"  - {repo.repo_name} (URL: {repo.repo_url}, User: {repo.user_id})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(create_test_repository())