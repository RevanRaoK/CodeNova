"""
Pytest configuration and shared fixtures for backend API tests.

This module provides:
- Common test fixtures
- Database setup and teardown
- Mock configurations
- Test utilities
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.models.users import User


# Test database configuration
# Use environment variable or default to test database
import os
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:codenova_secure_password@localhost:5432/codenova_test_db")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.first_name = "Test"
    user.last_name = "User"
    user.role = Mock()
    user.role.value = "user"
    user.gemini_api_key = None
    user.is_active = True
    return user


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user for testing."""
    from app.models.users import UserRole
    
    user = Mock(spec=User)
    user.id = 2
    user.email = "admin@example.com"
    user.full_name = "Admin User"
    user.first_name = "Admin"
    user.last_name = "User"
    user.role = UserRole.ADMIN  # Use actual enum value
    user.gemini_api_key = "encrypted_admin_key"
    user.is_active = True
    return user


@pytest.fixture
def mock_redis():
    """Create a mock Redis client for testing."""
    redis_mock = Mock()
    redis_mock.ping.return_value = True
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.exists.return_value = False
    redis_mock.expire.return_value = True
    return redis_mock


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency for testing."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client, mock_user, override_get_db):
    """Create an authenticated test client."""
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(client, mock_admin_user, override_get_db):
    """Create an admin authenticated test client."""
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    yield client
    app.dependency_overrides.clear()


# Test data fixtures
@pytest.fixture
def sample_user_profile():
    """Sample user profile data for testing."""
    return {
        "id": 1,
        "email": "test@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "jobTitle": "Software Developer",
        "bio": "Experienced developer",
        "programmingLanguages": ["python", "javascript", "java"],
        "profilePictureUrl": None
    }


@pytest.fixture
def sample_user_preferences():
    """Sample user preferences data for testing."""
    return {
        "theme": "dark",
        "language": "en",
        "timezone": "UTC",
        "defaultProgrammingLanguage": "python",
        "aiModel": "gemini-pro",
        "codeEditorTheme": "vs-dark",
        "autoSave": True,
        "showLineNumbers": True
    }


@pytest.fixture
def sample_analytics_data():
    """Sample analytics data for testing."""
    return {
        "totalReviews": 25,
        "totalAnalyses": 30,
        "successRate": 85.5,
        "recentActivity": [
            {
                "type": "analysis",
                "timestamp": "2024-01-15T10:30:00Z",
                "description": "Code review completed"
            }
        ],
        "usageTrends": {
            "timeframe": "30d",
            "data": [
                {"date": "2024-01-01", "reviews": 5, "acceptances": 4},
                {"date": "2024-01-02", "reviews": 3, "acceptances": 2}
            ]
        },
        "feedbackDistribution": {
            "accepted": 15,
            "rejected": 5,
            "modified": 5,
            "total": 25
        }
    }


# Utility functions for tests
def create_mock_file(filename: str, content: bytes, content_type: str, size: int = None):
    """Create a mock file for upload testing."""
    from io import BytesIO
    
    mock_file = Mock()
    mock_file.filename = filename
    mock_file.content_type = content_type
    mock_file.size = size or len(content)
    mock_file.file = BytesIO(content)
    mock_file.read = lambda: content
    return mock_file


def assert_response_success(response, expected_status=200):
    """Assert that a response is successful."""
    assert response.status_code == expected_status
    assert response.json() is not None


def assert_response_error(response, expected_status, expected_message=None):
    """Assert that a response contains an error."""
    assert response.status_code == expected_status
    data = response.json()
    assert "detail" in data
    if expected_message:
        assert expected_message.lower() in data["detail"].lower()


# Performance testing utilities
class PerformanceTimer:
    """Utility class for measuring test performance."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start the timer."""
        from datetime import datetime
        self.start_time = datetime.utcnow()
    
    def stop(self):
        """Stop the timer."""
        from datetime import datetime
        self.end_time = datetime.utcnow()
    
    def duration(self):
        """Get the duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def assert_duration_under(self, max_seconds):
        """Assert that the duration is under the specified seconds."""
        duration = self.duration()
        assert duration is not None, "Timer was not properly started/stopped"
        assert duration < max_seconds, f"Operation took {duration}s, expected under {max_seconds}s"


@pytest.fixture
def performance_timer():
    """Provide a performance timer for tests."""
    return PerformanceTimer()


# Database testing utilities
def create_test_user(db_session, **kwargs):
    """Create a test user in the database."""
    from app.models.users import User
    
    user_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "hashed_password": "hashed_password",
        **kwargs
    }
    
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_test_analysis(db_session, user_id, **kwargs):
    """Create a test analysis record in the database."""
    from app.models.analysis import Analysis
    
    analysis_data = {
        "user_id": user_id,
        "filename": "test.py",
        "content": "print('hello')",
        "status": "completed",
        **kwargs
    }
    
    analysis = Analysis(**analysis_data)
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


# Mock service configurations
@pytest.fixture
def mock_analytics_service():
    """Create a mock analytics service."""
    service = Mock()
    service.get_user_stats = AsyncMock()
    service.get_usage_trends = AsyncMock()
    service.get_feedback_distribution = AsyncMock()
    service.get_dashboard_data = AsyncMock()
    return service


@pytest.fixture
def mock_user_service():
    """Create a mock user service."""
    service = Mock()
    service.get_user_profile = AsyncMock()
    service.update_user_profile = AsyncMock()
    service.get_user_preferences = AsyncMock()
    service.update_user_preferences = AsyncMock()
    service.get_api_key_status = AsyncMock()
    service.save_api_key = AsyncMock()
    service.validate_api_key = AsyncMock()
    service.delete_api_key = AsyncMock()
    return service


@pytest.fixture
def mock_batch_processing_service():
    """Create a mock batch processing service."""
    service = Mock()
    service.process_multiple_files = AsyncMock()
    service.get_batch_status = AsyncMock()
    service.get_batch_results = AsyncMock()
    return service


# Test markers for categorizing tests
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "api: mark test as an API test")
    config.addinivalue_line("markers", "database: mark test as requiring database")
    config.addinivalue_line("markers", "redis: mark test as requiring Redis")