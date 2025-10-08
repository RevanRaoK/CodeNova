import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Repository, Analysis, Feedback
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import tempfile
import os

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_e2e.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_test_db():
    """Setup test database"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Async test client fixture"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def test_user_data():
    """Test user data fixture"""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }

@pytest.fixture
def admin_user_data():
    """Admin user data fixture"""
    return {
        "email": "admin@example.com", 
        "password": "adminpassword123",
        "full_name": "Admin User",
        "role": "admin"
    }

class TestEndToEndIntegration:
    """End-to-end integration tests covering complete user workflows"""
    
    def test_complete_user_registration_and_login_workflow(self, client, setup_test_db, test_user_data):
        """Test complete user registration and login workflow"""
        # Step 1: Register new user
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200
        registration_data = response.json()
        assert "access_token" in registration_data
        assert registration_data["user"]["email"] == test_user_data["email"]
        
        # Step 2: Login with registered user
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login-json", json=login_data)
        assert response.status_code == 200
        login_response = response.json()
        assert "access_token" in login_response
        
        # Step 3: Access protected endpoint with token
        headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == test_user_data["email"]

    def test_complete_file_analysis_workflow(self, client, setup_test_db, test_user_data):
        """Test complete file upload and analysis workflow"""
        # Step 1: Register and login user
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login-json", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Upload file
        test_file_content = "console.log('Hello World');"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(test_file_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/v1/files/upload",
                    files={"file": ("test.js", upload_file, "text/javascript")},
                    headers=headers
                )
        
        os.unlink(f.name)
        assert response.status_code == 200
        upload_data = response.json()
        file_id = upload_data["id"]
        
        # Step 3: Trigger analysis
        response = client.post(f"/api/v1/analysis/analyze/{file_id}", headers=headers)
        assert response.status_code == 200
        analysis_data = response.json()
        analysis_id = analysis_data["id"]
        
        # Step 4: Get analysis results
        response = client.get(f"/api/v1/analysis/{analysis_id}", headers=headers)
        assert response.status_code == 200
        results = response.json()
        assert results["status"] in ["completed", "processing"]

    def test_feedback_submission_and_analytics_workflow(self, client, setup_test_db, test_user_data):
        """Test feedback submission and analytics workflow"""
        # Setup: Register user and create analysis
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login-json", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 1: Submit feedback
        feedback_data = {
            "suggestion_id": "test-suggestion-1",
            "action": "reject",
            "rejection_reasons": ["incorrect", "not_applicable"],
            "custom_reason": "This suggestion doesn't fit our coding standards"
        }
        response = client.post("/api/v1/feedback/submit", json=feedback_data, headers=headers)
        assert response.status_code == 200
        feedback_response = response.json()
        assert feedback_response["action"] == "reject"
        
        # Step 2: Get feedback analytics
        response = client.get("/api/v1/analytics/feedback", headers=headers)
        assert response.status_code == 200
        analytics_data = response.json()
        assert "acceptance_rate" in analytics_data
        assert "rejection_patterns" in analytics_data

    def test_github_integration_workflow(self, client, setup_test_db, test_user_data):
        """Test GitHub integration workflow"""
        # Setup: Register and login user
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login-json", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 1: Connect GitHub repository
        repo_data = {
            "repo_url": "https://github.com/testuser/testrepo",
            "access_token": "mock_github_token"
        }
        response = client.post("/api/v1/github/connect-repository", json=repo_data, headers=headers)
        assert response.status_code == 200
        repo_response = response.json()
        repo_id = repo_response["id"]
        
        # Step 2: Get connected repositories
        response = client.get("/api/v1/github/repositories", headers=headers)
        assert response.status_code == 200
        repos = response.json()
        assert len(repos) > 0
        assert any(repo["id"] == repo_id for repo in repos)

    def test_admin_user_management_workflow(self, client, setup_test_db, admin_user_data, test_user_data):
        """Test admin user management workflow"""
        # Step 1: Register admin user
        client.post("/api/v1/auth/register", json=admin_user_data)
        login_response = client.post("/api/v1/auth/login-json", json={
            "email": admin_user_data["email"],
            "password": admin_user_data["password"]
        })
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Step 2: Create regular user as admin
        response = client.post("/api/v1/admin/users", json=test_user_data, headers=admin_headers)
        assert response.status_code == 200
        created_user = response.json()
        user_id = created_user["id"]
        
        # Step 3: Update user role
        role_update = {"role": "team_lead"}
        response = client.put(f"/api/v1/admin/users/{user_id}/role", json=role_update, headers=admin_headers)
        assert response.status_code == 200
        
        # Step 4: Get all users
        response = client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 2  # Admin + created user

    def test_file_storage_integration_workflow(self, client, setup_test_db, test_user_data):
        """Test file storage integration workflow"""
        # Setup: Register and login user
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login-json", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 1: Upload file to storage
        test_content = "function test() { return 'hello'; }"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(test_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/v1/storage/upload",
                    files={"file": ("storage_test.js", upload_file, "text/javascript")},
                    headers=headers
                )
        
        os.unlink(f.name)
        assert response.status_code == 200
        storage_data = response.json()
        file_id = storage_data["id"]
        
        # Step 2: List user files
        response = client.get("/api/v1/storage/files", headers=headers)
        assert response.status_code == 200
        files = response.json()
        assert len(files) > 0
        assert any(f["id"] == file_id for f in files)
        
        # Step 3: Get file download URL
        response = client.get(f"/api/v1/storage/files/{file_id}/download", headers=headers)
        assert response.status_code == 200
        download_data = response.json()
        assert "download_url" in download_data

    def test_analytics_dashboard_workflow(self, client, setup_test_db, test_user_data):
        """Test analytics dashboard data workflow"""
        # Setup: Register user and create some data
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login-json", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create some feedback data
        feedback_data = {
            "suggestion_id": "test-suggestion-1",
            "action": "accept"
        }
        client.post("/api/v1/feedback/submit", json=feedback_data, headers=headers)
        
        # Step 1: Get dashboard analytics
        response = client.get("/api/v1/analytics/dashboard", headers=headers)
        assert response.status_code == 200
        dashboard_data = response.json()
        assert "acceptance_rate" in dashboard_data
        assert "total_analyses" in dashboard_data
        assert "recent_feedback" in dashboard_data
        
        # Step 2: Get usage statistics
        response = client.get("/api/v1/analytics/usage", headers=headers)
        assert response.status_code == 200
        usage_data = response.json()
        assert "daily_usage" in usage_data
        assert "weekly_usage" in usage_data

    def test_user_settings_workflow(self, client, setup_test_db, test_user_data):
        """Test user settings and profile management workflow"""
        # Setup: Register and login user
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login-json", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 1: Update user profile
        profile_update = {
            "full_name": "Updated Test User",
            "preferences": {
                "theme": "dark",
                "notifications": True,
                "language": "en"
            }
        }
        response = client.put("/api/v1/users/profile", json=profile_update, headers=headers)
        assert response.status_code == 200
        
        # Step 2: Get updated profile
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["full_name"] == "Updated Test User"
        assert user_data["preferences"]["theme"] == "dark"
        
        # Step 3: Change password
        password_change = {
            "current_password": test_user_data["password"],
            "new_password": "newpassword123"
        }
        response = client.put("/api/v1/users/change-password", json=password_change, headers=headers)
        assert response.status_code == 200

    def test_error_handling_workflow(self, client, setup_test_db):
        """Test error handling across different endpoints"""
        # Test 1: Unauthorized access
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
        
        # Test 2: Invalid login credentials
        invalid_login = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login-json", json=invalid_login)
        assert response.status_code == 401
        
        # Test 3: Duplicate user registration
        user_data = {
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "Duplicate User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        
        # Test 4: Invalid file upload
        login_response = client.post("/api/v1/auth/login-json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post("/api/v1/files/upload", headers=headers)
        assert response.status_code == 422  # Missing file

    def test_monitoring_and_health_checks(self, client):
        """Test monitoring endpoints"""
        # Test 1: Health check
        response = client.get("/api/v1/monitoring/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # Test 2: System metrics
        response = client.get("/api/v1/monitoring/metrics")
        assert response.status_code == 200
        metrics_data = response.json()
        assert "uptime" in metrics_data
        assert "memory_usage" in metrics_data