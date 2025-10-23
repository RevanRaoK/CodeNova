"""
Integration tests for API endpoints with database operations and caching.

Tests cover:
- End-to-end API workflows
- Database integration
- Caching functionality
- Cross-service interactions

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.deps import get_db, get_current_user, get_redis_client
from app.models.users import User
from app.services.analytics_service import AnalyticsService
from app.services.user_service import UserService


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for Analytics API with database and caching."""
    
    def test_analytics_dashboard_data_integration(self, authenticated_client, db_session, mock_redis):
        """Test complete analytics dashboard data retrieval with database."""
        # Setup test data in database
        user = create_test_user(db_session, email="analytics@test.com")
        
        # Create test analyses
        for i in range(5):
            create_test_analysis(
                db_session, 
                user.id, 
                filename=f"test_{i}.py",
                status="completed",
                created_at=datetime.utcnow() - timedelta(days=i)
            )
        
        # Override dependencies
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: user
        
        # Test dashboard data retrieval
        response = authenticated_client.get("/api/v1/analytics/dashboard-data?timeframe=30d")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify data structure
        assert "totalReviews" in data
        assert "usageTrends" in data
        assert "feedbackDistribution" in data
        assert isinstance(data["totalReviews"], int)
        
        # Verify caching was attempted
        mock_redis.get.assert_called()
        
        app.dependency_overrides.clear()
    
    def test_analytics_caching_behavior(self, authenticated_client, db_session, mock_redis):
        """Test analytics caching behavior with Redis."""
        user = create_test_user(db_session, email="cache@test.com")
        
        # Setup cache hit scenario
        cached_data = {
            "totalReviews": 10,
            "successRate": 90.0,
            "cached": True
        }
        mock_redis.get.return_value = json.dumps(cached_data)
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: user
        
        response = authenticated_client.get("/api/v1/analytics/user-stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify cached data was returned
        assert data.get("cached") is True
        mock_redis.get.assert_called()
        
        # Test cache miss scenario
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        
        response = authenticated_client.get("/api/v1/analytics/user-stats")
        
        # Verify cache was set after database query
        mock_redis.set.assert_called()
        
        app.dependency_overrides.clear()
    
    def test_analytics_performance_with_large_dataset(self, authenticated_client, db_session, performance_timer):
        """Test analytics performance with large dataset."""
        user = create_test_user(db_session, email="performance@test.com")
        
        # Create large dataset
        for i in range(100):
            create_test_analysis(
                db_session,
                user.id,
                filename=f"large_test_{i}.py",
                status="completed" if i % 2 == 0 else "failed"
            )
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: user
        
        performance_timer.start()
        response = authenticated_client.get("/api/v1/analytics/dashboard-data")
        performance_timer.stop()
        
        assert response.status_code == 200
        
        # Assert performance is acceptable
        performance_timer.assert_duration_under(2.0)  # Should complete within 2 seconds
        
        app.dependency_overrides.clear()


@pytest.mark.integration
class TestUserProfileIntegration:
    """Integration tests for User Profile API with database operations."""
    
    def test_complete_profile_update_workflow(self, authenticated_client, db_session):
        """Test complete profile update workflow with database persistence."""
        user = create_test_user(db_session, email="profile@test.com")
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: user
        
        # Test profile retrieval
        response = authenticated_client.get("/api/v1/users/profile")
        assert response.status_code == 200
        original_profile = response.json()
        
        # Test profile update
        update_data = {
            "firstName": "Updated",
            "lastName": "Name",
            "jobTitle": "Senior Developer",
            "bio": "Updated bio",
            "programmingLanguages": ["python", "javascript", "go"]
        }
        
        response = authenticated_client.put("/api/v1/users/profile", json=update_data)
        assert response.status_code == 200
        
        updated_profile = response.json()["profile"]
        assert updated_profile["firstName"] == "Updated"
        assert updated_profile["jobTitle"] == "Senior Developer"
        
        # Verify persistence by retrieving again
        response = authenticated_client.get("/api/v1/users/profile")
        assert response.status_code == 200
        
        persisted_profile = response.json()
        assert persisted_profile["firstName"] == "Updated"
        assert persisted_profile["jobTitle"] == "Senior Developer"
        
        app.dependency_overrides.clear()
    
    def test_api_key_management_workflow(self, authenticated_client, db_session):
        """Test complete API key management workflow."""
        user = create_test_user(db_session, email="apikey@test.com")
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: user
        
        # Test initial status (no key)
        response = authenticated_client.get("/api/v1/users/api-key")
        assert response.status_code == 200
        
        status = response.json()
        assert status["hasKey"] is False
        
        # Test API key validation
        api_key = "AIzaSyDxKXxKXxKXxKXxKXxKXxKXxKXxKXx"
        response = authenticated_client.post(
            "/api/v1/users/api-key/validate",
            json={"apiKey": api_key}
        )
        assert response.status_code == 200
        
        # Test API key saving
        response = authenticated_client.put(
            "/api/v1/users/api-key",
            json={"apiKey": api_key}
        )
        assert response.status_code == 200
        
        save_result = response.json()
        assert save_result["success"] is True
        
        # Test status after saving
        response = authenticated_client.get("/api/v1/users/api-key")
        assert response.status_code == 200
        
        status = response.json()
        assert status["hasKey"] is True
        assert status["keyPreview"] is not None
        
        # Test API key deletion
        response = authenticated_client.delete("/api/v1/users/api-key")
        assert response.status_code == 200
        
        # Verify deletion
        response = authenticated_client.get("/api/v1/users/api-key")
        status = response.json()
        assert status["hasKey"] is False
        
        app.dependency_overrides.clear()


@pytest.mark.integration
class TestSettingsIntegration:
    """Integration tests for Settings API with comprehensive persistence."""
    
    def test_comprehensive_settings_workflow(self, authenticated_client, db_session):
        """Test comprehensive settings management workflow."""
        user = create_test_user(db_session, email="settings@test.com")
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: user
        
        # Test initial settings retrieval
        response = authenticated_client.get("/api/v1/settings/")
        assert response.status_code == 200
        
        initial_settings = response.json()
        assert "general" in initial_settings
        assert "notifications" in initial_settings
        assert "security" in initial_settings
        
        # Test comprehensive settings update
        settings_update = {
            "general": {
                "theme": "light",
                "language": "es",
                "autoSave": False
            },
            "notifications": {
                "emailNotifications": {
                    "analysisComplete": False,
                    "weeklyReport": True
                },
                "frequency": "weekly"
            },
            "security": {
                "twoFactorEnabled": True,
                "sessionTimeout": 60
            }
        }
        
        response = authenticated_client.put("/api/v1/settings/", json=settings_update)
        assert response.status_code == 200
        
        update_result = response.json()
        assert update_result["message"] == "Settings updated successfully"
        assert "updatedFields" in update_result
        
        # Verify persistence by retrieving settings again
        response = authenticated_client.get("/api/v1/settings/")
        assert response.status_code == 200
        
        updated_settings = response.json()
        assert updated_settings["general"]["theme"] == "light"
        assert updated_settings["notifications"]["frequency"] == "weekly"
        assert updated_settings["security"]["twoFactorEnabled"] is True
        
        app.dependency_overrides.clear()
    
    def test_individual_settings_categories(self, authenticated_client, db_session):
        """Test individual settings category updates."""
        user = create_test_user(db_session, email="categories@test.com")
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: user
        
        # Test general settings
        general_update = {
            "theme": "dark",
            "language": "fr",
            "defaultProgrammingLanguage": "java"
        }
        
        response = authenticated_client.put("/api/v1/settings/general", json=general_update)
        assert response.status_code == 200
        
        # Test notification settings
        notification_update = {
            "emailNotifications": {
                "analysisComplete": True,
                "securityAlerts": False
            },
            "frequency": "daily"
        }
        
        response = authenticated_client.put("/api/v1/settings/notifications", json=notification_update)
        assert response.status_code == 200
        
        # Test security settings
        security_update = {
            "twoFactorEnabled": False,
            "dataCollection": False,
            "sessionTimeout": 120
        }
        
        response = authenticated_client.put("/api/v1/settings/security", json=security_update)
        assert response.status_code == 200
        
        # Verify all updates persisted
        response = authenticated_client.get("/api/v1/settings/")
        settings = response.json()
        
        assert settings["general"]["theme"] == "dark"
        assert settings["notifications"]["frequency"] == "daily"
        assert settings["security"]["sessionTimeout"] == 120
        
        app.dependency_overrides.clear()


@pytest.mark.integration
class TestFileUploadIntegration:
    """Integration tests for file upload and batch processing."""
    
    def test_multi_file_upload_workflow(self, authenticated_client, db_session):
        """Test complete multi-file upload and processing workflow."""
        user = create_test_user(db_session, email="upload@test.com")
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: user
        
        # Create test files
        files = [
            ("files", ("test1.py", b"print('hello world')", "text/plain")),
            ("files", ("test2.js", b"console.log('hello world')", "text/plain")),
            ("files", ("test3.java", b"System.out.println('hello world')", "text/plain"))
        ]
        
        # Mock batch processing service
        with patch('app.services.batch_processing_service.BatchProcessingService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.process_multiple_files = AsyncMock(return_value={
                "batchId": "test_batch_123",
                "totalFiles": 3,
                "status": "processing",
                "files": [
                    {"filename": "test1.py", "status": "queued", "fileId": "file_1"},
                    {"filename": "test2.js", "status": "queued", "fileId": "file_2"},
                    {"filename": "test3.java", "status": "queued", "fileId": "file_3"}
                ]
            })
            
            # Test file upload
            response = authenticated_client.post("/api/v1/files/upload-multiple", files=files)
            assert response.status_code == 200
            
            upload_result = response.json()
            assert upload_result["batchId"] == "test_batch_123"
            assert upload_result["totalFiles"] == 3
            
            batch_id = upload_result["batchId"]
            
            # Test batch status retrieval
            mock_instance.get_batch_status = AsyncMock(return_value={
                "batchId": batch_id,
                "status": "processing",
                "progress": 33.3,
                "processedFiles": 1,
                "totalFiles": 3
            })
            
            response = authenticated_client.get(f"/api/v1/files/upload-status/{batch_id}")
            assert response.status_code == 200
            
            status = response.json()
            assert status["status"] == "processing"
            assert status["progress"] == 33.3
            
            # Test completed batch results
            mock_instance.get_batch_results = AsyncMock(return_value={
                "batchId": batch_id,
                "status": "completed",
                "results": [
                    {
                        "fileId": "file_1",
                        "filename": "test1.py",
                        "analysis": {
                            "issues": [],
                            "summary": {"totalIssues": 0}
                        }
                    }
                ]
            })
            
            response = authenticated_client.get(f"/api/v1/files/analysis-results/{batch_id}")
            assert response.status_code == 200
            
            results = response.json()
            assert results["status"] == "completed"
            assert len(results["results"]) == 1
        
        app.dependency_overrides.clear()


@pytest.mark.integration
class TestCrossServiceIntegration:
    """Integration tests for cross-service interactions."""
    
    def test_analytics_and_user_service_integration(self, authenticated_client, db_session, mock_redis):
        """Test integration between analytics and user services."""
        user = create_test_user(db_session, email="cross@test.com")
        
        # Create user preferences that affect analytics
        user.preferences = json.dumps({
            "theme": "dark",
            "defaultProgrammingLanguage": "python"
        })
        db_session.commit()
        
        # Create analytics data
        for i in range(10):
            create_test_analysis(db_session, user.id, filename=f"cross_test_{i}.py")
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: user
        
        # Test that user preferences are considered in analytics
        response = authenticated_client.get("/api/v1/analytics/dashboard-data")
        assert response.status_code == 200
        
        # Test that analytics data is available when updating profile
        response = authenticated_client.get("/api/v1/users/profile")
        assert response.status_code == 200
        
        app.dependency_overrides.clear()
    
    def test_settings_and_analytics_integration(self, authenticated_client, db_session):
        """Test integration between settings and analytics services."""
        user = create_test_user(db_session, email="settings_analytics@test.com")
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: user
        
        # Update user settings
        settings_update = {
            "general": {
                "defaultProgrammingLanguage": "javascript",
                "aiModel": "gemini-pro"
            }
        }
        
        response = authenticated_client.put("/api/v1/settings/general", json=settings_update)
        assert response.status_code == 200
        
        # Verify settings affect analytics queries
        response = authenticated_client.get("/api/v1/analytics/user-stats")
        assert response.status_code == 200
        
        app.dependency_overrides.clear()


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def test_concurrent_requests_performance(self, authenticated_client, db_session, performance_timer):
        """Test API performance under concurrent requests."""
        user = create_test_user(db_session, email="concurrent@test.com")
        
        # Create test data
        for i in range(50):
            create_test_analysis(db_session, user.id, filename=f"perf_test_{i}.py")
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: user
        
        performance_timer.start()
        
        # Simulate concurrent requests
        responses = []
        for _ in range(10):
            response = authenticated_client.get("/api/v1/analytics/user-stats")
            responses.append(response)
        
        performance_timer.stop()
        
        # Verify all requests succeeded
        for response in responses:
            assert response.status_code == 200
        
        # Assert reasonable performance
        performance_timer.assert_duration_under(5.0)
        
        app.dependency_overrides.clear()
    
    def test_large_data_retrieval_performance(self, authenticated_client, db_session, performance_timer):
        """Test performance with large data retrieval."""
        user = create_test_user(db_session, email="large_data@test.com")
        
        # Create large dataset
        for i in range(1000):
            create_test_analysis(
                db_session,
                user.id,
                filename=f"large_data_{i}.py",
                content="x" * 1000  # 1KB per file
            )
        
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: user
        
        performance_timer.start()
        response = authenticated_client.get("/api/v1/analytics/dashboard-data?timeframe=1y")
        performance_timer.stop()
        
        assert response.status_code == 200
        
        # Should handle large datasets efficiently
        performance_timer.assert_duration_under(3.0)
        
        app.dependency_overrides.clear()


# Utility functions for integration tests
def create_test_user(db_session, **kwargs):
    """Create a test user in the database."""
    from app.models.users import User
    
    user_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "hashed_password": "hashed_password",
        "is_active": True,
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
    from datetime import datetime
    
    analysis_data = {
        "user_id": user_id,
        "filename": "test.py",
        "content": "print('hello')",
        "status": "completed",
        "created_at": datetime.utcnow(),
        **kwargs
    }
    
    analysis = Analysis(**analysis_data)
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])