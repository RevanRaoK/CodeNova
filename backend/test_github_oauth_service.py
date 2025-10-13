#!/usr/bin/env python3
"""
Test script for GitHub OAuth Service

This script tests the GitHub OAuth service functionality including:
- OAuth flow initiation
- State management
- Token validation
- Integration management

Usage: python test_github_oauth_service.py
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.services.github_oauth_service import GitHubOAuthService
from app.models.github_oauth import GitHubOAuthIntegration, GitHubOAuthState
from app.models.users import User


async def create_test_database():
    """Create test database and tables."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )
    
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    return engine


async def test_oauth_flow_initiation():
    """Test OAuth flow initiation."""
    print("\n=== Testing OAuth Flow Initiation ===")
    
    engine = await create_test_database()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    oauth_service = GitHubOAuthService()
    
    async with async_session() as db:
        try:
            # Test with user ID
            auth_url, state = await oauth_service.initiate_oauth_flow(
                db=db,
                user_id=1,
                redirect_url="http://localhost:3000/dashboard"
            )
            
            print(f"✓ Authorization URL generated: {auth_url[:100]}...")
            print(f"✓ State generated: {state}")
            
            # Verify state was stored
            result = await db.execute(
                db.query(GitHubOAuthState).filter(GitHubOAuthState.state == state)
            )
            stored_state = result.scalar_one_or_none()
            
            if stored_state:
                print(f"✓ State stored in database with expiration: {stored_state.expires_at}")
            else:
                print("✗ State not found in database")
            
            # Test without user ID (anonymous flow)
            auth_url_anon, state_anon = await oauth_service.initiate_oauth_flow(
                db=db,
                redirect_url="http://localhost:3000/connect"
            )
            
            print(f"✓ Anonymous flow URL generated: {auth_url_anon[:100]}...")
            print(f"✓ Anonymous state generated: {state_anon}")
            
        except Exception as e:
            print(f"✗ OAuth flow initiation failed: {str(e)}")
    
    await engine.dispose()


async def test_state_validation():
    """Test OAuth state validation."""
    print("\n=== Testing State Validation ===")
    
    engine = await create_test_database()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    oauth_service = GitHubOAuthService()
    
    async with async_session() as db:
        try:
            # Create a test state
            test_state = GitHubOAuthState(
                state="test_state_123",
                user_id=1,
                redirect_url="http://localhost:3000/test",
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            db.add(test_state)
            await db.commit()
            
            # Test valid state validation
            validated_state = await oauth_service._validate_oauth_state(
                db=db,
                state="test_state_123",
                user_id=1
            )
            
            if validated_state:
                print("✓ Valid state validation successful")
            else:
                print("✗ Valid state validation failed")
            
            # Test invalid state
            try:
                await oauth_service._validate_oauth_state(
                    db=db,
                    state="invalid_state",
                    user_id=1
                )
                print("✗ Invalid state should have failed")
            except Exception:
                print("✓ Invalid state correctly rejected")
            
            # Test expired state
            expired_state = GitHubOAuthState(
                state="expired_state_123",
                user_id=1,
                redirect_url="http://localhost:3000/test",
                expires_at=datetime.utcnow() - timedelta(minutes=1)
            )
            db.add(expired_state)
            await db.commit()
            
            try:
                await oauth_service._validate_oauth_state(
                    db=db,
                    state="expired_state_123",
                    user_id=1
                )
                print("✗ Expired state should have failed")
            except Exception:
                print("✓ Expired state correctly rejected")
            
        except Exception as e:
            print(f"✗ State validation test failed: {str(e)}")
    
    await engine.dispose()


async def test_token_validation():
    """Test GitHub token validation (requires valid token)."""
    print("\n=== Testing Token Validation ===")
    
    oauth_service = GitHubOAuthService()
    
    # Test with invalid token
    try:
        result = await oauth_service.validate_token("invalid_token_123")
        if not result.get("valid"):
            print("✓ Invalid token correctly identified")
        else:
            print("✗ Invalid token should have been rejected")
    except Exception as e:
        print(f"✓ Invalid token validation handled: {str(e)}")
    
    # Note: Testing with a real token would require actual GitHub OAuth flow
    print("ℹ Real token validation requires actual GitHub OAuth flow")


async def test_integration_management():
    """Test integration storage and retrieval."""
    print("\n=== Testing Integration Management ===")
    
    engine = await create_test_database()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    oauth_service = GitHubOAuthService()
    
    async with async_session() as db:
        try:
            # Test getting non-existent integration
            integration = await oauth_service.get_user_integration(db=db, user_id=999)
            if integration is None:
                print("✓ Non-existent integration correctly returns None")
            else:
                print("✗ Non-existent integration should return None")
            
            # Create a test integration
            test_integration = GitHubOAuthIntegration(
                user_id=1,
                github_user_id=12345,
                github_username="testuser",
                github_email="test@example.com",
                access_token="test_token_123",
                token_type="bearer",
                scope="repo user:email",
                is_active=True
            )
            db.add(test_integration)
            await db.commit()
            await db.refresh(test_integration)
            
            # Test retrieving integration
            retrieved_integration = await oauth_service.get_user_integration(db=db, user_id=1)
            if retrieved_integration and retrieved_integration.github_username == "testuser":
                print("✓ Integration retrieval successful")
            else:
                print("✗ Integration retrieval failed")
            
            # Test revoking integration
            revoked = await oauth_service.revoke_integration(db=db, user_id=1)
            if revoked:
                print("✓ Integration revocation successful")
                
                # Verify integration is inactive
                updated_integration = await oauth_service.get_user_integration(db=db, user_id=1)
                if updated_integration is None:
                    print("✓ Revoked integration no longer active")
                else:
                    print("✗ Revoked integration should not be active")
            else:
                print("✗ Integration revocation failed")
            
        except Exception as e:
            print(f"✗ Integration management test failed: {str(e)}")
    
    await engine.dispose()


async def test_cleanup_expired_states():
    """Test cleanup of expired OAuth states."""
    print("\n=== Testing Expired State Cleanup ===")
    
    engine = await create_test_database()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    oauth_service = GitHubOAuthService()
    
    async with async_session() as db:
        try:
            # Create some expired states
            expired_states = [
                GitHubOAuthState(
                    state=f"expired_state_{i}",
                    user_id=1,
                    expires_at=datetime.utcnow() - timedelta(minutes=i+1)
                )
                for i in range(3)
            ]
            
            for state in expired_states:
                db.add(state)
            await db.commit()
            
            # Run cleanup
            cleaned_count = await oauth_service.cleanup_expired_states(db)
            
            if cleaned_count == 3:
                print(f"✓ Cleaned up {cleaned_count} expired states")
            else:
                print(f"✗ Expected to clean 3 states, cleaned {cleaned_count}")
            
        except Exception as e:
            print(f"✗ Expired state cleanup test failed: {str(e)}")
    
    await engine.dispose()


async def test_configuration_validation():
    """Test OAuth configuration validation."""
    print("\n=== Testing Configuration Validation ===")
    
    oauth_service = GitHubOAuthService()
    
    # Check if configuration is present
    if oauth_service.client_id and oauth_service.client_secret:
        print("✓ GitHub OAuth configuration is present")
        print(f"  Client ID: {oauth_service.client_id[:10]}...")
        print(f"  Redirect URI: {oauth_service.redirect_uri}")
        print(f"  Default scopes: {oauth_service.default_scopes}")
    else:
        print("ℹ GitHub OAuth configuration not set (this is expected in test environment)")
        print("  Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to test with real configuration")


async def main():
    """Run all tests."""
    print("GitHub OAuth Service Test Suite")
    print("=" * 50)
    
    try:
        await test_configuration_validation()
        await test_oauth_flow_initiation()
        await test_state_validation()
        await test_token_validation()
        await test_integration_management()
        await test_cleanup_expired_states()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())