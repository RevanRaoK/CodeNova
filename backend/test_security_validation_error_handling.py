"""
Test suite for security, validation, and error handling implementation.

This test file verifies:
- Enhanced RBAC system
- Input validation middleware
- Comprehensive error handling
- Retry mechanisms

Requirements covered: 12.1, 12.2, 12.3, 12.4, 12.5, 14.1, 14.5
"""

import pytest
import asyncio
from fastapi import HTTPException
from sqlalchemy.orm import Session

# Import our new modules
from app.core.permissions import (
    Permission,
    PermissionChecker,
    require_permission,
    require_role,
    ROLE_PERMISSIONS
)
from app.core.validation import (
    FileValidationService,
    CodeValidationService,
    validate_email,
    validate_password,
    sanitize_filename
)
from app.core.error_handlers import (
    BaseAPIException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    ConflictException,
    RateLimitException,
    ServiceUnavailableException,
    FileUploadException,
    AnalysisException,
    ErrorResponse,
    retry_on_failure
)
from app.models.users import User, UserRole


class TestRBACSystem:
    """Test Role-Based Access Control system."""
    
    def test_role_permissions_mapping(self):
        """Test that all roles have proper permissions."""
        # Check that all roles are defined
        assert UserRole.USER in ROLE_PERMISSIONS
        assert UserRole.DEVELOPER in ROLE_PERMISSIONS
        assert UserRole.TEAM_LEAD in ROLE_PERMISSIONS
        assert UserRole.ADMIN in ROLE_PERMISSIONS
        assert UserRole.GUEST in ROLE_PERMISSIONS
        
        # Check that admin has all permissions
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        assert len(admin_perms) == len(list(Permission))
        
        # Check that user has basic permissions
        user_perms = ROLE_PERMISSIONS[UserRole.USER]
        assert Permission.ANALYZE_CODE in user_perms
        assert Permission.VIEW_OWN_ANALYSES in user_perms
        assert Permission.UPLOAD_FILES in user_perms
        
        # Check that team lead has team permissions
        team_lead_perms = ROLE_PERMISSIONS[UserRole.TEAM_LEAD]
        assert Permission.VIEW_TEAM_ANALYSES in team_lead_perms
        assert Permission.MANAGE_TEAM_MEMBERS in team_lead_perms
        
        print("✓ Role permissions mapping is correct")
    
    def test_permission_checker(self):
        """Test PermissionChecker functionality."""
        # Create mock users
        admin_user = User(id=1, email="admin@test.com", role=UserRole.ADMIN, is_active=True)
        regular_user = User(id=2, email="user@test.com", role=UserRole.USER, is_active=True)
        inactive_user = User(id=3, email="inactive@test.com", role=UserRole.USER, is_active=False)
        
        # Test admin permissions
        assert PermissionChecker.has_permission(admin_user, Permission.VIEW_ALL_USERS)
        assert PermissionChecker.has_permission(admin_user, Permission.ANALYZE_CODE)
        
        # Test regular user permissions
        assert PermissionChecker.has_permission(regular_user, Permission.ANALYZE_CODE)
        assert not PermissionChecker.has_permission(regular_user, Permission.VIEW_ALL_USERS)
        
        # Test inactive user
        assert not PermissionChecker.has_permission(inactive_user, Permission.ANALYZE_CODE)
        
        # Test has_any_permission
        assert PermissionChecker.has_any_permission(
            regular_user,
            [Permission.ANALYZE_CODE, Permission.VIEW_ALL_USERS]
        )
        
        # Test has_all_permissions
        assert not PermissionChecker.has_all_permissions(
            regular_user,
            [Permission.ANALYZE_CODE, Permission.VIEW_ALL_USERS]
        )
        
        print("✓ PermissionChecker works correctly")
    
    def test_get_user_permissions(self):
        """Test getting all permissions for a user."""
        admin_user = User(id=1, email="admin@test.com", role=UserRole.ADMIN, is_active=True)
        regular_user = User(id=2, email="user@test.com", role=UserRole.USER, is_active=True)
        
        admin_perms = PermissionChecker.get_user_permissions(admin_user)
        user_perms = PermissionChecker.get_user_permissions(regular_user)
        
        assert len(admin_perms) > len(user_perms)
        assert Permission.VIEW_ALL_USERS in admin_perms
        assert Permission.VIEW_ALL_USERS not in user_perms
        
        print("✓ Get user permissions works correctly")


class TestFileValidation:
    """Test file validation service."""
    
    def test_allowed_extensions(self):
        """Test that allowed extensions are properly defined."""
        assert '.py' in FileValidationService.ALLOWED_EXTENSIONS
        assert '.js' in FileValidationService.ALLOWED_EXTENSIONS
        assert '.exe' not in FileValidationService.ALLOWED_EXTENSIONS
        
        print("✓ Allowed extensions are properly defined")
    
    def test_blocked_extensions(self):
        """Test that dangerous extensions are blocked."""
        assert '.exe' in FileValidationService.BLOCKED_EXTENSIONS
        assert '.dll' in FileValidationService.BLOCKED_EXTENSIONS
        assert '.bat' in FileValidationService.BLOCKED_EXTENSIONS
        
        print("✓ Blocked extensions are properly defined")
    
    def test_max_file_size(self):
        """Test file size limits."""
        assert FileValidationService.MAX_FILE_SIZE == 5 * 1024 * 1024  # 5MB
        assert FileValidationService.MAX_BATCH_SIZE == 10
        
        print("✓ File size limits are correct")


class TestCodeValidation:
    """Test code validation service."""
    
    def test_validate_code_length(self):
        """Test code length validation."""
        # Too short
        is_valid, error = CodeValidationService.validate_code("short", "python")
        assert not is_valid
        assert "at least" in error.lower()
        
        # Valid length
        is_valid, error = CodeValidationService.validate_code("print('hello world')", "python")
        assert is_valid
        assert error is None
        
        # Too long
        long_code = "x" * (CodeValidationService.MAX_CODE_LENGTH + 1)
        is_valid, error = CodeValidationService.validate_code(long_code, "python")
        assert not is_valid
        assert "exceeds" in error.lower()
        
        print("✓ Code length validation works correctly")
    
    def test_validate_language(self):
        """Test language validation."""
        # Valid language
        is_valid, error = CodeValidationService.validate_code("print('hello')", "python")
        assert is_valid
        
        # Invalid language
        is_valid, error = CodeValidationService.validate_code("print('hello')", "invalid_lang")
        assert not is_valid
        assert "not supported" in error.lower()
        
        print("✓ Language validation works correctly")
    
    def test_validate_filename(self):
        """Test filename validation."""
        # Valid filename
        is_valid, error = CodeValidationService.validate_code("print('hello world')", "python", "test.py")
        assert is_valid
        
        # Empty filename
        is_valid, error = CodeValidationService.validate_code("print('hello world')", "python", "")
        assert not is_valid
        assert "empty" in error.lower()
        
        # Path traversal
        is_valid, error = CodeValidationService.validate_code("print('hello world')", "python", "../test.py")
        assert not is_valid
        assert "path" in error.lower()
        
        # Invalid characters
        is_valid, error = CodeValidationService.validate_code("print('hello world')", "python", "test<>.py")
        assert not is_valid
        assert "invalid" in error.lower()
        
        print("✓ Filename validation works correctly")
    
    def test_detect_language(self):
        """Test language detection from filename."""
        assert CodeValidationService.detect_language("test.py") == "python"
        assert CodeValidationService.detect_language("test.js") == "javascript"
        assert CodeValidationService.detect_language("test.ts") == "typescript"
        assert CodeValidationService.detect_language("test.java") == "java"
        assert CodeValidationService.detect_language("test.cpp") == "cpp"
        
        print("✓ Language detection works correctly")


class TestInputValidation:
    """Test input validation utilities."""
    
    def test_validate_email(self):
        """Test email validation."""
        assert validate_email("test@example.com")
        assert validate_email("user.name@domain.co.uk")
        assert not validate_email("invalid.email")
        assert not validate_email("@example.com")
        assert not validate_email("test@")
        
        print("✓ Email validation works correctly")
    
    def test_validate_password(self):
        """Test password validation."""
        # Valid password
        is_valid, errors = validate_password("SecurePass123!")
        assert is_valid
        assert len(errors) == 0
        
        # Too short
        is_valid, errors = validate_password("Short1!")
        assert not is_valid
        assert any("8 characters" in err for err in errors)
        
        # No uppercase
        is_valid, errors = validate_password("lowercase123!")
        assert not is_valid
        assert any("uppercase" in err for err in errors)
        
        # No lowercase
        is_valid, errors = validate_password("UPPERCASE123!")
        assert not is_valid
        assert any("lowercase" in err for err in errors)
        
        # No digit
        is_valid, errors = validate_password("NoDigits!")
        assert not is_valid
        assert any("digit" in err for err in errors)
        
        # No special char
        is_valid, errors = validate_password("NoSpecial123")
        assert not is_valid
        assert any("special" in err for err in errors)
        
        # Common password
        is_valid, errors = validate_password("password")
        assert not is_valid
        assert any("common" in err for err in errors)
        
        print("✓ Password validation works correctly")
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Path traversal
        assert ".." not in sanitize_filename("../test.py")
        assert "/" not in sanitize_filename("path/to/file.py")
        assert "\\" not in sanitize_filename("path\\to\\file.py")
        
        # Dangerous characters
        sanitized = sanitize_filename("test<>:|?.py")
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert "|" not in sanitized
        assert "?" not in sanitized
        
        # Length limit
        long_name = "a" * 300 + ".py"
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255
        
        print("✓ Filename sanitization works correctly")


class TestErrorHandling:
    """Test error handling system."""
    
    def test_base_api_exception(self):
        """Test BaseAPIException."""
        exc = BaseAPIException(
            message="Test error",
            status_code=400,
            error_code="test_error",
            details={"field": "value"}
        )
        
        assert exc.message == "Test error"
        assert exc.status_code == 400
        assert exc.error_code == "test_error"
        assert exc.details["field"] == "value"
        
        print("✓ BaseAPIException works correctly")
    
    def test_validation_exception(self):
        """Test ValidationException."""
        exc = ValidationException("Invalid input", field="email")
        
        assert exc.status_code == 400
        assert exc.error_code == "validation_error"
        assert exc.details["field"] == "email"
        
        print("✓ ValidationException works correctly")
    
    def test_authentication_exception(self):
        """Test AuthenticationException."""
        exc = AuthenticationException()
        
        assert exc.status_code == 401
        assert exc.error_code == "authentication_error"
        
        print("✓ AuthenticationException works correctly")
    
    def test_authorization_exception(self):
        """Test AuthorizationException."""
        exc = AuthorizationException()
        
        assert exc.status_code == 403
        assert exc.error_code == "authorization_error"
        
        print("✓ AuthorizationException works correctly")
    
    def test_resource_not_found_exception(self):
        """Test ResourceNotFoundException."""
        exc = ResourceNotFoundException("User", 123)
        
        assert exc.status_code == 404
        assert exc.error_code == "resource_not_found"
        assert exc.details["resource"] == "User"
        assert exc.details["resource_id"] == "123"
        
        print("✓ ResourceNotFoundException works correctly")
    
    def test_rate_limit_exception(self):
        """Test RateLimitException."""
        exc = RateLimitException(retry_after=60)
        
        assert exc.status_code == 429
        assert exc.error_code == "rate_limit_exceeded"
        assert exc.details["retry_after"] == 60
        
        print("✓ RateLimitException works correctly")
    
    def test_error_response_creation(self):
        """Test ErrorResponse creation."""
        response = ErrorResponse.create(
            error_code="test_error",
            message="Test message",
            status_code=400,
            details={"key": "value"}
        )
        
        assert response["error"] == "test_error"
        assert response["message"] == "Test message"
        assert response["status_code"] == 400
        assert response["details"]["key"] == "value"
        assert "timestamp" in response
        assert "request_id" in response
        
        print("✓ ErrorResponse creation works correctly")
    
    def test_user_friendly_messages(self):
        """Test user-friendly error messages."""
        message = ErrorResponse.user_friendly_message("validation_error", "Technical error")
        assert "check your input" in message.lower()
        
        message = ErrorResponse.user_friendly_message("authentication_error", "Auth failed")
        assert "log in" in message.lower()
        
        message = ErrorResponse.user_friendly_message("authorization_error", "No permission")
        assert "permission" in message.lower()
        
        print("✓ User-friendly messages work correctly")


class TestRetryMechanism:
    """Test retry mechanism."""
    
    @pytest.mark.asyncio
    async def test_retry_on_failure_success(self):
        """Test retry mechanism with eventual success."""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.1, backoff=1)
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await flaky_operation()
        assert result == "success"
        assert call_count == 3
        
        print("✓ Retry mechanism works with eventual success")
    
    @pytest.mark.asyncio
    async def test_retry_on_failure_max_retries(self):
        """Test retry mechanism with max retries exceeded."""
        call_count = 0
        
        @retry_on_failure(max_retries=2, delay=0.1, backoff=1)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise Exception("Permanent failure")
        
        with pytest.raises(Exception) as exc_info:
            await always_fails()
        
        assert "Permanent failure" in str(exc_info.value)
        assert call_count == 3  # Initial + 2 retries
        
        print("✓ Retry mechanism respects max retries")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("Testing Security, Validation, and Error Handling")
    print("="*60 + "\n")
    
    # Test RBAC
    print("Testing RBAC System...")
    rbac_tests = TestRBACSystem()
    rbac_tests.test_role_permissions_mapping()
    rbac_tests.test_permission_checker()
    rbac_tests.test_get_user_permissions()
    print()
    
    # Test File Validation
    print("Testing File Validation...")
    file_tests = TestFileValidation()
    file_tests.test_allowed_extensions()
    file_tests.test_blocked_extensions()
    file_tests.test_max_file_size()
    print()
    
    # Test Code Validation
    print("Testing Code Validation...")
    code_tests = TestCodeValidation()
    code_tests.test_validate_code_length()
    code_tests.test_validate_language()
    code_tests.test_validate_filename()
    code_tests.test_detect_language()
    print()
    
    # Test Input Validation
    print("Testing Input Validation...")
    input_tests = TestInputValidation()
    input_tests.test_validate_email()
    input_tests.test_validate_password()
    input_tests.test_sanitize_filename()
    print()
    
    # Test Error Handling
    print("Testing Error Handling...")
    error_tests = TestErrorHandling()
    error_tests.test_base_api_exception()
    error_tests.test_validation_exception()
    error_tests.test_authentication_exception()
    error_tests.test_authorization_exception()
    error_tests.test_resource_not_found_exception()
    error_tests.test_rate_limit_exception()
    error_tests.test_error_response_creation()
    error_tests.test_user_friendly_messages()
    print()
    
    # Test Retry Mechanism
    print("Testing Retry Mechanism...")
    print("Note: Async tests require pytest-asyncio to run")
    print()
    
    print("="*60)
    print("All tests completed successfully!")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
