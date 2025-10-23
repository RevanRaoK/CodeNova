#!/usr/bin/env python3
"""
Comprehensive test suite for API Key Management System.

This test verifies all aspects of the API key management implementation:
- Encrypted storage of API keys
- API endpoints for saving, retrieving, and validating API keys
- API key masking for security
- Proper error handling and validation

Requirements tested: 4.8, 4.9, 6.6, 6.7, 6.8
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import application modules
from app.main import app
from app.core.database import Base, get_db
from app.models.users import User, UserRole
from app.services.user_service import UserService
from app.core.encryption import encrypt_api_key, decrypt_api_key, mask_api_key
from app.core.security import get_password_hash
from app.core.auth import get_current_user

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api_key_management.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

class TestAPIKeyManagement:
    """Test suite for API Key Management System."""
    
    def __init__(self):
        """Initialize test suite."""
        Base.metadata.create_all(bind=engine)
        self.user_service = UserService()
        self.db = TestingSessionLocal()
        
        # Create test user
        self.test_user = User(
            email="testuser@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("testpassword123"),
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            preferences={}
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)
        
        # Create admin user
        self.admin_user = User(
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("adminpassword123"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            preferences={}
        )
        self.db.add(self.admin_user)
        self.db.commit()
        self.db.refresh(self.admin_user)
    
    def cleanup(self):
        """Clean up test database."""
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    def get_auth_headers(self, user_id: int):
        """Get authentication headers for test user."""
        # Mock JWT token for testing
        with patch('app.core.auth.get_current_user') as mock_auth:
            if user_id == self.test_user.id:
                mock_auth.return_value = self.test_user
            else:
                mock_auth.return_value = self.admin_user
            return {"Authorization": f"Bearer test_token_{user_id}"}
    
    async def test_encryption_service(self):
        """Test encryption and decryption of API keys."""
        print("\n=== Testing Encryption Service ===")
        
        # Test data
        test_api_key = "AIzaSyDummyTestKey123456789"
        
        # Test encryption
        encrypted_key = encrypt_api_key(test_api_key)
        print(f"Original key: {test_api_key}")
        print(f"Encrypted key: {encrypted_key}")
        
        assert encrypted_key != test_api_key, "Key should be encrypted"
        assert len(encrypted_key) > len(test_api_key), "Encrypted key should be longer"
        
        # Test decryption
        decrypted_key = decrypt_api_key(encrypted_key)
        print(f"Decrypted key: {decrypted_key}")
        
        assert decrypted_key == test_api_key, "Decrypted key should match original"
        
        # Test masking
        masked_key = mask_api_key(test_api_key)
        print(f"Masked key: {masked_key}")
        
        assert masked_key != test_api_key, "Key should be masked"
        assert masked_key.endswith("789"), "Should show last 4 characters"
        assert "****" in masked_key, "Should contain asterisks"
        
        print("✅ Encryption service tests passed")
    
    async def test_api_key_validation(self):
        """Test API key validation logic."""
        print("\n=== Testing API Key Validation ===")
        
        # Test valid API key
        valid_key = "AIzaSyDummyTestKey123456789"
        result = await self.user_service.validate_api_key(valid_key)
        print(f"Valid key result: {result}")
        assert result["valid"] is True, "Valid key should pass validation"
        
        # Test invalid format - wrong prefix
        invalid_key = "InvalidKey123456789"
        result = await self.user_service.validate_api_key(invalid_key)
        print(f"Invalid prefix result: {result}")
        assert result["valid"] is False, "Invalid prefix should fail validation"
        assert "start with 'AIza'" in result["error"], "Should mention prefix requirement"
        
        # Test too short key
        short_key = "AIza123"
        result = await self.user_service.validate_api_key(short_key)
        print(f"Short key result: {result}")
        assert result["valid"] is False, "Short key should fail validation"
        assert "at least 10 characters" in result["error"], "Should mention length requirement"
        
        # Test empty key
        result = await self.user_service.validate_api_key("")
        print(f"Empty key result: {result}")
        assert result["valid"] is False, "Empty key should fail validation"
        
        # Test None key
        result = await self.user_service.validate_api_key(None)
        print(f"None key result: {result}")
        assert result["valid"] is False, "None key should fail validation"
        
        print("✅ API key validation tests passed")
    
    async def test_save_api_key(self):
        """Test saving API key to database."""
        print("\n=== Testing Save API Key ===")
        
        test_api_key = "AIzaSyTestSaveKey123456789"
        
        # Test saving valid API key
        result = await self.user_service.save_api_key(self.db, self.test_user.id, test_api_key)
        print(f"Save result: {result}")
        
        assert result["success"] is True, "Save should succeed"
        assert "saved successfully" in result["message"], "Should have success message"
        assert result["keyPreview"] != test_api_key, "Should return masked preview"
        assert result["keyPreview"].endswith("789"), "Preview should show last 4 chars"
        
        # Verify key is encrypted in database
        self.db.refresh(self.test_user)
        assert self.test_user.gemini_api_key is not None, "API key should be saved"
        assert self.test_user.gemini_api_key != test_api_key, "API key should be encrypted"
        
        # Test saving invalid API key
        try:
            await self.user_service.save_api_key(self.db, self.test_user.id, "invalid_key")
            assert False, "Should raise exception for invalid key"
        except HTTPException as e:
            print(f"Invalid key error: {e.detail}")
            assert e.status_code == 400, "Should return 400 for invalid key"
            assert "start with 'AIza'" in e.detail, "Should mention format requirement"
        
        print("✅ Save API key tests passed")
    
    async def test_get_api_key_status(self):
        """Test getting API key status."""
        print("\n=== Testing Get API Key Status ===")
        
        # Test user with API key
        result = await self.user_service.get_api_key_status(self.db, self.test_user.id)
        print(f"Status with key: {result}")
        
        assert result["hasKey"] is True, "Should indicate user has key"
        assert result["keyPreview"] is not None, "Should provide key preview"
        assert "****" in result["keyPreview"], "Preview should be masked"
        
        # Test user without API key
        result = await self.user_service.get_api_key_status(self.db, self.admin_user.id)
        print(f"Status without key: {result}")
        
        assert result["hasKey"] is False, "Should indicate user has no key"
        assert result["keyPreview"] is None, "Should not provide preview"
        
        print("✅ Get API key status tests passed")
    
    async def test_get_decrypted_api_key(self):
        """Test getting decrypted API key for internal use."""
        print("\n=== Testing Get Decrypted API Key ===")
        
        # Test user with API key
        decrypted_key = await self.user_service.get_decrypted_api_key(self.db, self.test_user.id)
        print(f"Decrypted key: {decrypted_key}")
        
        assert decrypted_key is not None, "Should return decrypted key"
        assert decrypted_key.startswith("AIza"), "Should be valid API key format"
        
        # Test user without API key
        decrypted_key = await self.user_service.get_decrypted_api_key(self.db, self.admin_user.id)
        print(f"No key result: {decrypted_key}")
        
        assert decrypted_key is None, "Should return None for user without key"
        
        print("✅ Get decrypted API key tests passed")
    
    async def test_delete_api_key(self):
        """Test deleting API key."""
        print("\n=== Testing Delete API Key ===")
        
        # Test deleting existing API key
        result = await self.user_service.delete_api_key(self.db, self.test_user.id)
        print(f"Delete result: {result}")
        
        assert result["success"] is True, "Delete should succeed"
        assert "deleted successfully" in result["message"], "Should have success message"
        
        # Verify key is removed from database
        self.db.refresh(self.test_user)
        assert self.test_user.gemini_api_key is None, "API key should be removed"
        
        # Test deleting non-existent API key
        try:
            await self.user_service.delete_api_key(self.db, self.test_user.id)
            assert False, "Should raise exception for non-existent key"
        except HTTPException as e:
            print(f"No key error: {e.detail}")
            assert e.status_code == 400, "Should return 400 for no key"
            assert "No API key to delete" in e.detail, "Should mention no key exists"
        
        print("✅ Delete API key tests passed")
    
    def test_api_endpoints(self):
        """Test API endpoints for key management."""
        print("\n=== Testing API Endpoints ===")
        
        # Override the dependency to return our test user
        def override_get_current_user():
            return self.test_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            # Test get API key status (no key)
            response = client.get("/api/v1/users/api-key")
            print(f"GET status response: {response.status_code}, {response.json()}")
            assert response.status_code == 200
            data = response.json()
            assert data["hasKey"] is False
            
            # Test validate API key
            response = client.post(
                "/api/v1/users/api-key/validate",
                json={"apiKey": "AIzaSyTestEndpointKey123456789"}
            )
            print(f"POST validate response: {response.status_code}, {response.json()}")
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            
            # Test validate invalid API key
            response = client.post(
                "/api/v1/users/api-key/validate",
                json={"apiKey": "invalid_key"}
            )
            print(f"POST validate invalid response: {response.status_code}, {response.json()}")
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            
            # Test save API key
            response = client.put(
                "/api/v1/users/api-key",
                json={"apiKey": "AIzaSyTestEndpointKey123456789"}
            )
            print(f"PUT save response: {response.status_code}, {response.json()}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "keyPreview" in data
            
            # Test get API key status (with key)
            response = client.get("/api/v1/users/api-key")
            print(f"GET status with key response: {response.status_code}, {response.json()}")
            assert response.status_code == 200
            data = response.json()
            assert data["hasKey"] is True
            assert data["keyPreview"] is not None
            
            # Test delete API key
            response = client.delete("/api/v1/users/api-key")
            print(f"DELETE response: {response.status_code}, {response.json()}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Test get API key status (after deletion)
            response = client.get("/api/v1/users/api-key")
            print(f"GET status after delete response: {response.status_code}, {response.json()}")
            assert response.status_code == 200
            data = response.json()
            assert data["hasKey"] is False
            
        finally:
            # Clean up dependency override
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]
        
        print("✅ API endpoints tests passed")
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        print("\n=== Testing Error Handling ===")
        
        # Override the dependency to return our test user
        def override_get_current_user():
            return self.test_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            # Test save with invalid JSON
            response = client.put(
                "/api/v1/users/api-key",
                json={"apiKey": ""}  # Empty key
            )
            print(f"Empty key response: {response.status_code}, {response.json()}")
            assert response.status_code == 422  # Validation error
            
            # Test save with missing field
            response = client.put(
                "/api/v1/users/api-key",
                json={}  # Missing apiKey field
            )
            print(f"Missing field response: {response.status_code}, {response.json()}")
            assert response.status_code == 422  # Validation error
            
            # Test save with too short key
            response = client.put(
                "/api/v1/users/api-key",
                json={"apiKey": "short"}
            )
            print(f"Short key response: {response.status_code}, {response.json()}")
            assert response.status_code == 422  # Validation error from Pydantic
            
        finally:
            # Clean up dependency override
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]
        
        print("✅ Error handling tests passed")
    
    async def run_all_tests(self):
        """Run all test methods."""
        print("🚀 Starting API Key Management System Tests")
        print("=" * 60)
        
        try:
            await self.test_encryption_service()
            await self.test_api_key_validation()
            await self.test_save_api_key()
            await self.test_get_api_key_status()
            await self.test_get_decrypted_api_key()
            await self.test_delete_api_key()
            self.test_api_endpoints()
            self.test_error_handling()
            
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED! API Key Management System is working correctly.")
            print("\n✅ Requirements verified:")
            print("   - 4.8: API key configuration and encryption ✓")
            print("   - 4.9: API key validation and error handling ✓")
            print("   - 6.6: API key status retrieval ✓")
            print("   - 6.7: API key saving and validation ✓")
            print("   - 6.8: API key deletion and security ✓")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.cleanup()

def main():
    """Main test runner."""
    test_suite = TestAPIKeyManagement()
    asyncio.run(test_suite.run_all_tests())

if __name__ == "__main__":
    main()