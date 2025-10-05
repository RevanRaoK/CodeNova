"""
Comprehensive test suite for UserService functionality.
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.services.user_service import UserService
from app.models.users import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserRoleUpdate
from app.core.exceptions import ValidationError, NotFoundError, ConflictError


class TestUserService:
    """Test suite for UserService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.user_service = UserService(self.mock_db)
        
        # Sample user data
        self.sample_user = User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed_password",
            role=UserRole.USER,
            is_active=True,
            is_verified=False,
            preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @patch('app.services.user_service.get_password_hash')
    def test_create_user_success(self, mock_hash):
        """Test successful user creation."""
        mock_hash.return_value = "hashed_password"
        self.mock_db.query().filter().first.return_value = None
        
        user_data = UserCreate(
            email="new@example.com",
            full_name="New User",
            password="SecurePass123"
        )
        
        result = self.user_service.create_user(user_data)
        
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        mock_hash.assert_called_once_with("SecurePass123")
    
    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email."""
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        user_data = UserCreate(
            email="test@example.com",
            full_name="Another User",
            password="SecurePass123"
        )
        
        with pytest.raises(ConflictError):
            self.user_service.create_user(user_data)
    
    def test_create_oauth_user_new(self):
        """Test creating new OAuth user."""
        self.mock_db.query().filter().first.return_value = None
        
        result = self.user_service.create_oauth_user(
            email="oauth@example.com",
            full_name="OAuth User",
            oauth_provider="google",
            oauth_id="12345",
            profile_picture_url="https://example.com/pic.jpg"
        )
        
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_create_oauth_user_existing(self):
        """Test OAuth user creation when user already exists."""
        existing_user = User(
            id=1,
            email="oauth@example.com",
            full_name="Existing User",
            oauth_provider=None,
            oauth_id=None
        )
        self.mock_db.query().filter().first.return_value = existing_user
        
        result = self.user_service.create_oauth_user(
            email="oauth@example.com",
            full_name="OAuth User",
            oauth_provider="google",
            oauth_id="12345"
        )
        
        assert existing_user.oauth_provider == "google"
        assert existing_user.oauth_id == "12345"
        self.mock_db.commit.assert_called_once()
    
    @patch('app.services.user_service.verify_password')
    def test_authenticate_user_success(self, mock_verify):
        """Test successful user authentication."""
        mock_verify.return_value = True
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.authenticate_user("test@example.com", "password")
        
        assert result == self.sample_user
        assert self.sample_user.last_login is not None
        mock_verify.assert_called_once_with("password", "hashed_password")
    
    @patch('app.services.user_service.verify_password')
    def test_authenticate_user_wrong_password(self, mock_verify):
        """Test authentication with wrong password."""
        mock_verify.return_value = False
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.authenticate_user("test@example.com", "wrong_password")
        
        assert result is None
    
    def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user."""
        self.mock_db.query().filter().first.return_value = None
        
        result = self.user_service.authenticate_user("nonexistent@example.com", "password")
        
        assert result is None
    
    def test_get_user_by_id(self):
        """Test getting user by ID."""
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.get_user_by_id(1)
        
        assert result == self.sample_user
    
    def test_get_user_by_email(self):
        """Test getting user by email."""
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.get_user_by_email("test@example.com")
        
        assert result == self.sample_user
    
    def test_update_user_success(self):
        """Test successful user update."""
        # Mock the get_user_by_id call to return the sample user
        # Mock the get_user_by_email call to return None (no conflict)
        self.mock_db.query().filter().first.side_effect = [self.sample_user, None]
        
        update_data = UserUpdate(
            full_name="Updated Name",
            email="updated@example.com"
        )
        
        result = self.user_service.update_user(1, update_data)
        
        assert self.sample_user.full_name == "Updated Name"
        assert self.sample_user.email == "updated@example.com"
        self.mock_db.commit.assert_called_once()
    
    def test_update_user_not_found(self):
        """Test updating non-existent user."""
        self.mock_db.query().filter().first.return_value = None
        
        update_data = UserUpdate(full_name="Updated Name")
        
        with pytest.raises(NotFoundError):
            self.user_service.update_user(999, update_data)
    
    def test_update_user_role(self):
        """Test updating user role."""
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        role_data = UserRoleUpdate(role=UserRole.ADMIN)
        
        result = self.user_service.update_user_role(1, role_data)
        
        assert self.sample_user.role == UserRole.ADMIN
        self.mock_db.commit.assert_called_once()
    
    def test_update_user_preferences(self):
        """Test updating user preferences."""
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        preferences = {"theme": "dark", "notifications": True}
        
        result = self.user_service.update_user_preferences(1, preferences)
        
        assert self.sample_user.preferences == preferences
        self.mock_db.commit.assert_called_once()
    
    def test_deactivate_user(self):
        """Test user deactivation."""
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.deactivate_user(1)
        
        assert self.sample_user.is_active is False
        self.mock_db.commit.assert_called_once()
    
    def test_activate_user(self):
        """Test user activation."""
        self.sample_user.is_active = False
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.activate_user(1)
        
        assert self.sample_user.is_active is True
        self.mock_db.commit.assert_called_once()
    
    def test_verify_user_email(self):
        """Test email verification."""
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.verify_user_email(1)
        
        assert self.sample_user.is_verified is True
        self.mock_db.commit.assert_called_once()
    
    def test_get_users_by_role(self):
        """Test getting users by role."""
        users = [self.sample_user]
        self.mock_db.query().filter().offset().limit().all.return_value = users
        
        result = self.user_service.get_users_by_role(UserRole.USER)
        
        assert result == users
    
    def test_search_users(self):
        """Test user search functionality."""
        users = [self.sample_user]
        self.mock_db.query().filter().offset().limit().all.return_value = users
        
        result = self.user_service.search_users("test")
        
        assert result == users
    
    def test_get_user_count(self):
        """Test getting total user count."""
        self.mock_db.query().count.return_value = 5
        
        result = self.user_service.get_user_count()
        
        assert result == 5
    
    def test_delete_user(self):
        """Test user deletion."""
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.delete_user(1)
        
        assert result is True
        self.mock_db.delete.assert_called_once_with(self.sample_user)
        self.mock_db.commit.assert_called_once()
    
    @patch('app.services.user_service.verify_password')
    @patch('app.services.user_service.get_password_hash')
    def test_change_password_success(self, mock_hash, mock_verify):
        """Test successful password change."""
        mock_verify.return_value = True
        mock_hash.return_value = "new_hashed_password"
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.change_password(1, "old_password", "new_password")
        
        assert self.sample_user.hashed_password == "new_hashed_password"
        mock_verify.assert_called_once_with("old_password", "hashed_password")
        mock_hash.assert_called_once_with("new_password")
    
    @patch('app.services.user_service.verify_password')
    def test_change_password_wrong_current(self, mock_verify):
        """Test password change with wrong current password."""
        mock_verify.return_value = False
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        with pytest.raises(ValidationError):
            self.user_service.change_password(1, "wrong_password", "new_password")
    
    def test_assign_user_to_team(self):
        """Test assigning user to team."""
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.assign_user_to_team(1, "team-123")
        
        assert self.sample_user.team_id == "team-123"
        self.mock_db.commit.assert_called_once()
    
    def test_remove_user_from_team(self):
        """Test removing user from team."""
        self.sample_user.team_id = "team-123"
        self.mock_db.query().filter().first.return_value = self.sample_user
        
        result = self.user_service.remove_user_from_team(1)
        
        assert self.sample_user.team_id is None
        self.mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])