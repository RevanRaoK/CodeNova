#!/usr/bin/env python3
"""
Integration test for API Key Management with AI Service.

This test verifies that the AI service correctly uses user's personal API keys
when available, and falls back to the default key when not available.

Requirements tested: 4.8, 6.8 (AI service integration)
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import application modules
from app.core.database import Base
from app.models.users import User, UserRole
from app.services.user_service import UserService
from app.services.ai_service import AIService, get_ai_service_for_user
from app.core.security import get_password_hash
from app.core.encryption import encrypt_api_key

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api_key_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestAPIKeyIntegration:
    """Test suite for API Key Integration with AI Service."""
    
    def __init__(self):
        """Initialize test suite."""
        Base.metadata.create_all(bind=engine)
        self.user_service = UserService()
        self.db = TestingSessionLocal()
        
        # Create test user without API key
        self.user_no_key = User(
            email="nokey@example.com",
            full_name="No Key User",
            hashed_password=get_password_hash("testpassword123"),
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            preferences={}
        )
        self.db.add(self.user_no_key)
        self.db.commit()
        self.db.refresh(self.user_no_key)
        
        # Create test user with API key
        self.user_with_key = User(
            email="withkey@example.com",
            full_name="With Key User",
            hashed_password=get_password_hash("testpassword123"),
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            preferences={},
            gemini_api_key=encrypt_api_key("AIzaSyUserPersonalKey123456789")
        )
        self.db.add(self.user_with_key)
        self.db.commit()
        self.db.refresh(self.user_with_key)
    
    def cleanup(self):
        """Clean up test database."""
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    def test_ai_service_with_user_key(self):
        """Test that AI service uses user's personal API key when available."""
        print("\n=== Testing AI Service with User API Key ===")
        
        # Test user with personal API key
        ai_service = get_ai_service_for_user(user_id=self.user_with_key.id, db=self.db)
        print(f"AI service for user with key: {ai_service}")
        print(f"AI service API key: {ai_service.api_key}")
        
        assert ai_service is not None, "Should return AI service instance"
        assert ai_service.api_key == "AIzaSyUserPersonalKey123456789", "Should use user's personal API key"
        
        print("✅ AI service correctly uses user's personal API key")
    
    def test_ai_service_without_user_key(self):
        """Test that AI service falls back to default key when user has no personal key."""
        print("\n=== Testing AI Service without User API Key ===")
        
        # Test user without personal API key
        ai_service = get_ai_service_for_user(user_id=self.user_no_key.id, db=self.db)
        print(f"AI service for user without key: {ai_service}")
        print(f"AI service API key: {ai_service.api_key}")
        
        assert ai_service is not None, "Should return AI service instance"
        # Should use default API key from settings
        from app.core.config import settings
        assert ai_service.api_key == settings.GEMINI_API_KEY, "Should use default API key"
        
        print("✅ AI service correctly falls back to default API key")
    
    async def test_ai_service_key_switching(self):
        """Test that AI service switches keys when user adds/removes personal key."""
        print("\n=== Testing AI Service Key Switching ===")
        
        # Initially user has no key
        ai_service_before = get_ai_service_for_user(user_id=self.user_no_key.id, db=self.db)
        from app.core.config import settings
        assert ai_service_before.api_key == settings.GEMINI_API_KEY, "Should use default key initially"
        
        # Add personal API key
        test_key = "AIzaSyNewPersonalKey987654321"
        result = await self.user_service.save_api_key(self.db, self.user_no_key.id, test_key)
        assert result["success"] is True, "Should successfully save API key"
        
        # Now AI service should use personal key
        ai_service_after = get_ai_service_for_user(user_id=self.user_no_key.id, db=self.db)
        assert ai_service_after.api_key == test_key, "Should use personal API key after saving"
        
        # Remove personal API key
        delete_result = await self.user_service.delete_api_key(self.db, self.user_no_key.id)
        assert delete_result["success"] is True, "Should successfully delete API key"
        
        # Should fall back to default key
        ai_service_final = get_ai_service_for_user(user_id=self.user_no_key.id, db=self.db)
        assert ai_service_final.api_key == settings.GEMINI_API_KEY, "Should fall back to default key after deletion"
        
        print("✅ AI service correctly switches between personal and default keys")
    
    def test_ai_service_error_handling(self):
        """Test AI service error handling with corrupted API keys."""
        print("\n=== Testing AI Service Error Handling ===")
        
        # Create user with corrupted API key
        corrupted_user = User(
            email="corrupted@example.com",
            full_name="Corrupted Key User",
            hashed_password=get_password_hash("testpassword123"),
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            preferences={},
            gemini_api_key="corrupted_encrypted_key_that_cannot_be_decrypted"
        )
        self.db.add(corrupted_user)
        self.db.commit()
        self.db.refresh(corrupted_user)
        
        # AI service should handle decryption error gracefully
        ai_service = get_ai_service_for_user(user_id=corrupted_user.id, db=self.db)
        print(f"AI service with corrupted key: {ai_service}")
        
        assert ai_service is not None, "Should return AI service instance even with corrupted key"
        from app.core.config import settings
        assert ai_service.api_key == settings.GEMINI_API_KEY, "Should fall back to default key on decryption error"
        
        print("✅ AI service correctly handles corrupted API keys")
    
    async def test_complete_workflow(self):
        """Test complete workflow: save key -> use in AI service -> validate -> delete."""
        print("\n=== Testing Complete Workflow ===")
        
        user_id = self.user_no_key.id
        test_api_key = "AIzaSyWorkflowTestKey123456789"
        
        # Step 1: Save API key
        print("Step 1: Saving API key...")
        save_result = await self.user_service.save_api_key(self.db, user_id, test_api_key)
        assert save_result["success"] is True
        print(f"✓ API key saved: {save_result['keyPreview']}")
        
        # Step 2: Verify AI service uses the key
        print("Step 2: Verifying AI service uses personal key...")
        ai_service = get_ai_service_for_user(user_id=user_id, db=self.db)
        assert ai_service.api_key == test_api_key
        print("✓ AI service using personal API key")
        
        # Step 3: Check API key status
        print("Step 3: Checking API key status...")
        status = await self.user_service.get_api_key_status(self.db, user_id)
        assert status["hasKey"] is True
        assert status["keyPreview"] is not None
        print(f"✓ API key status: {status}")
        
        # Step 4: Get decrypted key (internal use)
        print("Step 4: Getting decrypted key for internal use...")
        decrypted = await self.user_service.get_decrypted_api_key(self.db, user_id)
        assert decrypted == test_api_key
        print("✓ Decrypted key matches original")
        
        # Step 5: Delete API key
        print("Step 5: Deleting API key...")
        delete_result = await self.user_service.delete_api_key(self.db, user_id)
        assert delete_result["success"] is True
        print("✓ API key deleted")
        
        # Step 6: Verify AI service falls back to default
        print("Step 6: Verifying fallback to default key...")
        ai_service_after = get_ai_service_for_user(user_id=user_id, db=self.db)
        from app.core.config import settings
        assert ai_service_after.api_key == settings.GEMINI_API_KEY
        print("✓ AI service using default key after deletion")
        
        print("✅ Complete workflow test passed")
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("🚀 Starting API Key Integration Tests")
        print("=" * 60)
        
        try:
            self.test_ai_service_with_user_key()
            self.test_ai_service_without_user_key()
            await self.test_ai_service_key_switching()
            self.test_ai_service_error_handling()
            await self.test_complete_workflow()
            
            print("\n" + "=" * 60)
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("\n✅ API Key Management System fully integrated with AI Service:")
            print("   - Personal API keys are used when available ✓")
            print("   - Fallback to default key works correctly ✓")
            print("   - Key switching works seamlessly ✓")
            print("   - Error handling is robust ✓")
            print("   - Complete workflow functions properly ✓")
            
        except Exception as e:
            print(f"\n❌ INTEGRATION TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.cleanup()

def main():
    """Main test runner."""
    import asyncio
    test_suite = TestAPIKeyIntegration()
    asyncio.run(test_suite.run_all_tests())

if __name__ == "__main__":
    main()