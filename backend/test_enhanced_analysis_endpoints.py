"""
Integration tests for enhanced analysis endpoints with feedback integration.

Tests cover:
- Enhanced analyze-code endpoint with feedback interface
- Issue retrieval endpoints
- AST integration and issue ID generation

Requirements covered: 1.1, 1.2, 1.3, 1.4, 5.1, 5.2
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.users import User
from app.models.analysis import DirectAnalysis
from app.models.feedback import Issue, FeedbackRecord
from app.core.security import create_access_token
import uuid
from datetime import datetime, timedelta

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_enhanced_analysis.db"
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

@pytest.fixture(scope="function")
def setup_database():
    """Set up test database with tables."""
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after each test
    db = TestingSessionLocal()
    try:
        # Delete all records in reverse order to handle foreign keys
        db.query(Issue).delete()
        db.query(DirectAnalysis).delete()
        db.query(User).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

@pytest.fixture
def test_user():
    """Create a test user for authentication."""
    db = TestingSessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            return existing_user
        
        user = User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            hashed_password="fake_hashed_password",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        # If user creation fails due to constraint, try to get existing user
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            return existing_user
        raise e
    finally:
        db.close()

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test requests."""
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def sample_code():
    """Sample code for testing analysis."""
    return """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total

class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)
    
    def get_total(self):
        return calculate_total(self.items)
"""

class TestEnhancedAnalysisEndpoint:
    """Test enhanced analyze-code endpoint with feedback integration."""
    
    def test_analyze_code_with_feedback_interface(self, setup_database, auth_headers, sample_code):
        """Test that analyze-code endpoint returns feedback interface information."""
        response = client.post(
            "/api/v1/analysis/analyze-code",
            json={
                "code": sample_code,
                "language": "python",
                "filename": "shopping_cart.py"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic analysis response
        assert "analysis_id" in data
        assert data["status"] == "completed"
        assert "issues" in data
        assert "metrics" in data
        assert "summary" in data
        
        # Verify feedback interface is included
        assert "feedback_interface" in data
        feedback_interface = data["feedback_interface"]
        
        assert feedback_interface["enabled"] is True
        assert "feedback_endpoint" in feedback_interface
        assert "issue_retrieval_endpoint" in feedback_interface
        assert "analysis_issues_endpoint" in feedback_interface
        assert "supported_feedback_types" in feedback_interface
        assert "feedback_instructions" in feedback_interface
        
        # Verify supported feedback types
        supported_types = feedback_interface["supported_feedback_types"]
        assert "accept" in supported_types
        assert "reject" in supported_types
        assert "modify" in supported_types
        
        # Verify AST processing information
        assert "ast_processing" in data
        ast_processing = data["ast_processing"]
        assert "enabled" in ast_processing
        assert "processing_time_seconds" in ast_processing
        assert "patterns_detected" in ast_processing
        assert "language_supported" in ast_processing
    
    def test_analyze_code_creates_issue_records(self, setup_database, auth_headers, sample_code):
        """Test that analyze-code endpoint creates Issue records in database."""
        response = client.post(
            "/api/v1/analysis/analyze-code",
            json={
                "code": sample_code,
                "language": "python",
                "filename": "test.py"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        analysis_id = data["analysis_id"]
        
        # Verify issues were created in database
        db = TestingSessionLocal()
        try:
            issues = db.query(Issue).filter(Issue.analysis_id == analysis_id).all()
            assert len(issues) > 0
            
            # Verify issue structure
            for issue in issues:
                assert issue.id is not None
                assert len(issue.id) == 64  # SHA-256 hash length
                assert issue.analysis_id == analysis_id
                assert issue.pattern_type is not None
                assert issue.severity in ["info", "warning", "error"]
                assert issue.suggestion_text is not None
                assert issue.status == "active"
                assert issue.location is not None
        finally:
            db.close()
    
    def test_analyze_code_with_ast_integration(self, setup_database, auth_headers):
        """Test AST integration in analyze-code endpoint."""
        python_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    def add(self, a, b):
        return a + b
"""
        
        response = client.post(
            "/api/v1/analysis/analyze-code",
            json={
                "code": python_code,
                "language": "python",
                "filename": "fibonacci.py"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify AST processing information
        ast_processing = data["ast_processing"]
        assert ast_processing["language_supported"] is True
        assert "processing_time_seconds" in ast_processing
        
        # Verify issues have unique IDs
        issues = data["issues"]
        issue_ids = [issue["id"] for issue in issues]
        assert len(issue_ids) == len(set(issue_ids))  # All IDs should be unique


class TestIssueRetrievalEndpoints:
    """Test issue retrieval endpoints."""
    
    @pytest.fixture
    def sample_analysis_with_issues(self, setup_database, test_user, sample_code):
        """Create a sample analysis with issues for testing."""
        db = TestingSessionLocal()
        try:
            # Create analysis
            analysis_id = str(uuid.uuid4())
            analysis = DirectAnalysis(
                id=analysis_id,
                user_id=test_user.id,
                code_content=sample_code,
                language="python",
                filename="test.py",
                status="completed",
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                results={"issues": [], "metrics": {}},
                lines_of_code=10,
                issues_count=2
            )
            db.add(analysis)
            
            # Create issues
            issue1 = Issue(
                id="a" * 64,  # 64-character ID
                analysis_id=analysis_id,
                pattern_type="function_complexity",
                severity="warning",
                category="ai-review",
                location={"line": 5, "column": 1},
                suggestion_text="Consider simplifying this function",
                code_context="def complex_function():",
                status="active",
                confidence_score=0.8
            )
            
            issue2 = Issue(
                id="b" * 64,  # 64-character ID
                analysis_id=analysis_id,
                pattern_type="naming_convention",
                severity="info",
                category="style",
                location={"line": 10, "column": 5},
                suggestion_text="Use snake_case for variable names",
                code_context="camelCaseVar = 1",
                status="active",
                confidence_score=0.9
            )
            
            db.add(issue1)
            db.add(issue2)
            db.commit()
            
            return {
                "analysis_id": analysis_id,
                "issue1_id": issue1.id,
                "issue2_id": issue2.id
            }
        finally:
            db.close()
    
    def test_get_issue_by_id(self, setup_database, auth_headers, sample_analysis_with_issues):
        """Test retrieving a specific issue by ID."""
        issue_id = sample_analysis_with_issues["issue1_id"]
        
        response = client.get(
            f"/api/v1/analysis/issues/{issue_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify issue details
        assert data["issue_id"] == issue_id
        assert data["analysis_id"] == sample_analysis_with_issues["analysis_id"]
        assert data["pattern_type"] == "function_complexity"
        assert data["severity"] == "warning"
        assert data["suggestion_text"] == "Consider simplifying this function"
        assert data["status"] == "active"
        
        # Verify feedback summary
        assert "feedback_summary" in data
        feedback_summary = data["feedback_summary"]
        assert "total_feedback" in feedback_summary
        assert "accepted" in feedback_summary
        assert "rejected" in feedback_summary
        assert "modified" in feedback_summary
        
        # Verify feedback interface
        assert "feedback_interface" in data
        feedback_interface = data["feedback_interface"]
        assert feedback_interface["can_provide_feedback"] is True
        assert "supported_actions" in feedback_interface
    
    def test_get_issue_by_id_not_found(self, setup_database, auth_headers):
        """Test retrieving non-existent issue returns 404."""
        response = client.get(
            "/api/v1/analysis/issues/nonexistent_id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_analysis_issues(self, setup_database, auth_headers, sample_analysis_with_issues):
        """Test retrieving all issues for an analysis."""
        analysis_id = sample_analysis_with_issues["analysis_id"]
        
        response = client.get(
            f"/api/v1/analysis/analyses/{analysis_id}/issues",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["analysis_id"] == analysis_id
        assert "issues" in data
        assert "pagination" in data
        assert "summary" in data
        assert "feedback_interface" in data
        
        # Verify issues
        issues = data["issues"]
        assert len(issues) == 2
        
        # Verify pagination
        pagination = data["pagination"]
        assert pagination["total_count"] == 2
        assert pagination["page"] == 1
        assert pagination["has_next"] is False
        assert pagination["has_previous"] is False
        
        # Verify summary statistics
        summary = data["summary"]
        assert summary["total_issues"] == 2
        assert "severity_distribution" in summary
        assert "status_distribution" in summary
        assert "pattern_distribution" in summary
    
    def test_get_analysis_issues_with_filters(self, setup_database, auth_headers, sample_analysis_with_issues):
        """Test retrieving analysis issues with filters."""
        analysis_id = sample_analysis_with_issues["analysis_id"]
        
        # Filter by severity
        response = client.get(
            f"/api/v1/analysis/analyses/{analysis_id}/issues?severity=warning",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        issues = data["issues"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"
        
        # Verify filters are reflected in response
        assert data["filters"]["severity"] == "warning"
    
    def test_get_analysis_issues_pagination(self, setup_database, auth_headers, sample_analysis_with_issues):
        """Test pagination in analysis issues endpoint."""
        analysis_id = sample_analysis_with_issues["analysis_id"]
        
        response = client.get(
            f"/api/v1/analysis/analyses/{analysis_id}/issues?page=1&page_size=1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination
        pagination = data["pagination"]
        assert pagination["page_size"] == 1
        assert pagination["total_count"] == 2
        assert pagination["has_next"] is True
        assert len(data["issues"]) == 1
    
    def test_get_analysis_issues_not_found(self, setup_database, auth_headers):
        """Test retrieving issues for non-existent analysis returns 404."""
        response = client.get(
            "/api/v1/analysis/analyses/nonexistent_id/issues",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestErrorHandling:
    """Test error handling in enhanced endpoints."""
    
    def test_analyze_code_invalid_language(self, setup_database, auth_headers):
        """Test analyze-code with invalid language."""
        response = client.post(
            "/api/v1/analysis/analyze-code",
            json={
                "code": "print('hello')",
                "language": "invalid_language",
                "filename": "test.py"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422
        assert "Unsupported language" in response.json()["detail"][0]["msg"]
    
    def test_analyze_code_empty_code(self, setup_database, auth_headers):
        """Test analyze-code with empty code."""
        response = client.post(
            "/api/v1/analysis/analyze-code",
            json={
                "code": "",
                "language": "python",
                "filename": "test.py"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"][0]["msg"]
        assert "at least 1 character" in error_detail or "cannot be empty" in error_detail
    
    def test_analyze_code_too_large(self, setup_database, auth_headers):
        """Test analyze-code with code that's too large."""
        # Create code that exceeds the 100KB limit
        large_code = "# " + "x" * 102400  # 102KB of comments
        
        response = client.post(
            "/api/v1/analysis/analyze-code",
            json={
                "code": large_code,
                "language": "python",
                "filename": "test.py"
            },
            headers=auth_headers
        )
        
        # Print response for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        # Should return 413 for our custom size check or 422 for Pydantic validation
        assert response.status_code in [413, 422]
        
        response_data = response.json()
        response_detail = response_data["detail"]
        
        if isinstance(response_detail, str):
            # String error message
            assert any(keyword in response_detail.lower() 
                      for keyword in ["too large", "string too long", "exceeds maximum", "100kb"])
        elif isinstance(response_detail, list):
            # Pydantic validation error format (list of error objects)
            error_messages = []
            for error in response_detail:
                if isinstance(error, dict):
                    # Get the message from the error dict
                    msg = error.get("msg", "")
                    error_messages.append(str(msg).lower())
                    # Also check the 'type' field which might contain relevant info
                    error_type = error.get("type", "")
                    error_messages.append(str(error_type).lower())
                else:
                    error_messages.append(str(error).lower())
            
            # Check if any error message contains size-related keywords
            size_keywords = ["too long", "too large", "exceeds maximum", "100kb", "string_too_long", "max_length"]
            assert any(keyword in msg for msg in error_messages for keyword in size_keywords), \
                f"Expected size-related error, got: {error_messages}"
        else:
            # Fallback - just check that we got an error response
            assert response.status_code in [413, 422]
    
    def test_unauthorized_access(self, setup_database):
        """Test endpoints without authentication."""
        response = client.post(
            "/api/v1/analysis/analyze-code",
            json={
                "code": "print('hello')",
                "language": "python"
            }
        )
        
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])