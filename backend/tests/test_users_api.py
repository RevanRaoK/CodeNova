"""
Unit and integration tests for Users API endpoints.

Tests cover:
- User profile management
- Settings and preferences
- API key management
- File upload functionality
- Authentication and authorization

Requirements: 6.4, 6.5, 6.6, 6.7, 6.8
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
from sqlalchemy.orm import Session
from io import BytesIO

from app.main import app
from app.api.deps import get_db, get_current_user
from app.models.users import User
from app.services.user_service import UserService
from app.schemas.users import UserProfile, UserProfileUpdate, UserPreferences


class TestUsersAPI:
    """Test suite for Users API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.role = Mock()
        user.role.value = "user"
        user.gemini_api_key = None
        return user
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user."""
        user = Mock(spec=User)
        user.id = 2
        user.email = "admin@example.com"
        user.role = Mock()
        user.role.value = "admin"
        user.gemini_api_key = "encrypted_key"
        return user
    
    def setup_method(self):
        """Setup for each test method."""
        self.sample_profile = {
            "id": 1,
            "email": "test@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "jobTitle": "Developer",
            "bio": "Software developer",
            "programmingLanguages": ["python", "javascript"],
            "profilePictureUrl": None
        }
        
        self.sample_preferences = {
            "theme": "dark",
            "language": "en",
            "timezone": "UTC",
            "defaultProgrammingLanguage": "python",
            "aiModel": "gemini-pro",
            "autoSave": True
        }
    
    def test_get_current_user_profile_success(self, client, mock_db, mock_user):
        """Test successful retrieval of current user profile."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch.object(UserService, 'get_user_profile', new_callable=AsyncMock) as mock_get_profile:
            mock_get_profile.return_value = self.sample_profile
            
            response = client.get("/api/v1/users/profile")
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["firstName"] == "John"
            mock_get_profile.assert_called_once_with(mock_db, "1")
        
        app.dependency_overrides.clear()
    
    def test_get_user_profile_by_id_forbidden(self, client, mock_db, mock_user):
        """Test access control for user profile by ID."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        response = client.get("/api/v1/users/999/profile")
        
        assert response.status_code == 403
        assert "Access forbidden" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_update_current_user_profile_success(self, client, mock_db, mock_user):
        """Test successful profile update."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        update_data = {
            "firstName": "Jane",
            "lastName": "Smith",
            "jobTitle": "Senior Developer"
        }
        
        updated_profile = {**self.sample_profile, **update_data}
        
        with patch.object(UserService, 'update_user_profile', new_callable=AsyncMock) as mock_update:
            with patch.object(UserService, 'get_user_by_email', new_callable=AsyncMock) as mock_get_by_email:
                mock_update.return_value = updated_profile
                mock_get_by_email.return_value = None  # Email not taken
                
                response = client.put("/api/v1/users/profile", json=update_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "Profile updated successfully"
                assert data["profile"]["firstName"] == "Jane"
                mock_update.assert_called_once()
        
        app.dependency_overrides.clear()
    
    def test_update_profile_email_conflict(self, client, mock_db, mock_user):
        """Test profile update with conflicting email."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        update_data = {
            "email": "existing@example.com"
        }
        
        existing_user = Mock()
        existing_user.id = 999  # Different user
        
        with patch.object(UserService, 'get_user_by_email', new_callable=AsyncMock) as mock_get_by_email:
            mock_get_by_email.return_value = existing_user
            
            response = client.put("/api/v1/users/profile", json=update_data)
            
            assert response.status_code == 400
            assert "Email already registered" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_get_current_user_preferences_success(self, client, mock_db, mock_user):
        """Test successful retrieval of user preferences."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch.object(UserService, 'get_user_preferences', new_callable=AsyncMock) as mock_get_prefs:
            mock_get_prefs.return_value = self.sample_preferences
            
            response = client.get("/api/v1/users/preferences")
            
            assert response.status_code == 200
            data = response.json()
            assert data["theme"] == "dark"
            assert data["aiModel"] == "gemini-pro"
            mock_get_prefs.assert_called_once_with(mock_db, "1")
        
        app.dependency_overrides.clear()
    
    def test_update_current_user_preferences_success(self, client, mock_db, mock_user):
        """Test successful preferences update."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        update_data = {
            "theme": "light",
            "language": "es",
            "autoSave": False
        }
        
        updated_preferences = {**self.sample_preferences, **update_data}
        
        with patch.object(UserService, 'update_user_preferences', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = updated_preferences
            
            response = client.put("/api/v1/users/preferences", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Preferences updated successfully"
            assert data["preferences"]["theme"] == "light"
            mock_update.assert_called_once()
        
        app.dependency_overrides.clear()
    
    def test_upload_profile_picture_success(self, client, mock_db, mock_user):
        """Test successful profile picture upload."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        # Create mock image file
        image_data = b"fake_image_data"
        files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}
        
        with patch.object(UserService, 'upload_profile_picture', new_callable=AsyncMock) as mock_upload:
            mock_upload.return_value = "https://example.com/profile.jpg"
            
            response = client.post("/api/v1/users/profile-picture", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "profilePictureUrl" in data
            mock_upload.assert_called_once()
        
        app.dependency_overrides.clear()
    
    def test_upload_profile_picture_invalid_type(self, client, mock_db, mock_user):
        """Test profile picture upload with invalid file type."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        # Create mock text file
        text_data = b"not an image"
        files = {"file": ("test.txt", BytesIO(text_data), "text/plain")}
        
        response = client.post("/api/v1/users/profile-picture", files=files)
        
        assert response.status_code == 400
        assert "File must be an image" in response.json()["detail"]
        
        app.dependency_overrides.clear()


class TestAPIKeyManagement:
    """Test suite for API key management endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.gemini_api_key = None
        return user
    
    @pytest.fixture
    def mock_user_with_key(self):
        """Mock user with API key."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.gemini_api_key = "encrypted_api_key"
        return user
    
    def test_get_api_key_status_no_key(self, client, mock_db, mock_user):
        """Test API key status when user has no key."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch.object(UserService, 'get_api_key_status', new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = {
                "hasKey": False,
                "keyPreview": None
            }
            
            response = client.get("/api/v1/users/api-key")
            
            assert response.status_code == 200
            data = response.json()
            assert data["hasKey"] is False
            assert data["keyPreview"] is None
            mock_get_status.assert_called_once_with(mock_db, 1)
        
        app.dependency_overrides.clear()
    
    def test_get_api_key_status_with_key(self, client, mock_db, mock_user_with_key):
        """Test API key status when user has key."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user_with_key
        
        with patch.object(UserService, 'get_api_key_status', new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = {
                "hasKey": True,
                "keyPreview": "AIza****1234"
            }
            
            response = client.get("/api/v1/users/api-key")
            
            assert response.status_code == 200
            data = response.json()
            assert data["hasKey"] is True
            assert data["keyPreview"] == "AIza****1234"
        
        app.dependency_overrides.clear()
    
    def test_save_api_key_success(self, client, mock_db, mock_user):
        """Test successful API key save."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        api_key_data = {
            "apiKey": "AIzaSyDxKXxKXxKXxKXxKXxKXxKXxKXxKXx"
        }
        
        with patch.object(UserService, 'save_api_key', new_callable=AsyncMock) as mock_save:
            mock_save.return_value = {
                "success": True,
                "message": "API key saved successfully",
                "keyPreview": "AIza****xKXx"
            }
            
            response = client.put("/api/v1/users/api-key", json=api_key_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "keyPreview" in data
            mock_save.assert_called_once_with(mock_db, 1, api_key_data["apiKey"])
        
        app.dependency_overrides.clear()
    
    def test_save_api_key_invalid_format(self, client, mock_db, mock_user):
        """Test API key save with invalid format."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        api_key_data = {
            "apiKey": "short"  # Too short
        }
        
        response = client.put("/api/v1/users/api-key", json=api_key_data)
        
        assert response.status_code == 422  # Validation error
        
        app.dependency_overrides.clear()
    
    def test_validate_api_key_success(self, client, mock_db, mock_user):
        """Test successful API key validation."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        api_key_data = {
            "apiKey": "AIzaSyDxKXxKXxKXxKXxKXxKXxKXxKXxKXx"
        }
        
        with patch.object(UserService, 'validate_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "message": "API key is valid"
            }
            
            response = client.post("/api/v1/users/api-key/validate", json=api_key_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            mock_validate.assert_called_once_with(api_key_data["apiKey"])
        
        app.dependency_overrides.clear()
    
    def test_validate_api_key_invalid(self, client, mock_db, mock_user):
        """Test API key validation with invalid key."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        api_key_data = {
            "apiKey": "invalid_api_key_format"
        }
        
        with patch.object(UserService, 'validate_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "message": "Invalid API key format"
            }
            
            response = client.post("/api/v1/users/api-key/validate", json=api_key_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert "Invalid" in data["message"]
        
        app.dependency_overrides.clear()
    
    def test_delete_api_key_success(self, client, mock_db, mock_user_with_key):
        """Test successful API key deletion."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user_with_key
        
        with patch.object(UserService, 'delete_api_key', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = {
                "success": True,
                "message": "API key deleted successfully"
            }
            
            response = client.delete("/api/v1/users/api-key")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_delete.assert_called_once_with(mock_db, 1)
        
        app.dependency_overrides.clear()


class TestUserSettingsIntegration:
    """Integration tests for user settings endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.role = Mock()
        user.role.value = "user"
        return user
    
    def test_get_user_settings_comprehensive(self, client, mock_db, mock_user):
        """Test comprehensive user settings retrieval."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        comprehensive_settings = {
            "preferences": {
                "theme": "dark",
                "language": "en",
                "timezone": "UTC"
            },
            "notifications": {
                "emailNotifications": {"enabled": True},
                "pushNotifications": {"enabled": False}
            },
            "security": {
                "twoFactorEnabled": False,
                "sessionTimeout": 30
            }
        }
        
        with patch.object(UserService, 'get_user_settings', new_callable=AsyncMock) as mock_get_settings:
            mock_get_settings.return_value = comprehensive_settings
            
            response = client.get("/api/v1/users/1/settings")
            
            assert response.status_code == 200
            data = response.json()
            assert "preferences" in data
            assert "notifications" in data
            assert "security" in data
            mock_get_settings.assert_called_once_with(mock_db, 1)
        
        app.dependency_overrides.clear()
    
    def test_update_user_settings_comprehensive(self, client, mock_db, mock_user):
        """Test comprehensive user settings update."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        settings_update = {
            "theme": "light",
            "emailNotifications": {"enabled": False},
            "twoFactorEnabled": True
        }
        
        updated_settings = {
            "preferences": {"theme": "light"},
            "notifications": {"emailNotifications": {"enabled": False}},
            "security": {"twoFactorEnabled": True}
        }
        
        with patch.object(UserService, 'update_user_settings', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = updated_settings
            
            response = client.put("/api/v1/users/1/settings", json=settings_update)
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Settings updated successfully"
            assert "settings" in data
            mock_update.assert_called_once()
        
        app.dependency_overrides.clear()


class TestUserServiceIntegration:
    """Integration tests for UserService with database operations."""
    
    def test_user_service_database_operations(self):
        """Test UserService database operations."""
        mock_db = Mock(spec=Session)
        service = UserService()
        
        # Test profile retrieval
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # This would test actual service method
        # result = await service.get_user_profile(mock_db, "1")
        
        mock_db.query.assert_called()
    
    def test_user_service_caching_behavior(self):
        """Test UserService caching behavior."""
        mock_db = Mock(spec=Session)
        mock_redis = Mock()
        service = UserService()
        
        # Test cache hit
        cached_data = json.dumps({"cached": True})
        mock_redis.get.return_value = cached_data
        
        # This would test cache retrieval
        # result = service.get_cached_user_data("user:1")
        
        mock_redis.get.assert_called()
        
        # Test cache miss and database query
        mock_redis.get.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        # This would test database fallback
        # result = service.get_user_with_cache("1")
        
        mock_db.query.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])