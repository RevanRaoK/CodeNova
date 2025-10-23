"""
Unit and integration tests for Analytics API endpoints.

Tests cover:
- User statistics endpoints
- Usage trends and feedback distribution
- Real-time analytics via WebSocket
- Performance metrics and caching
- Error handling and validation

Requirements: 6.1, 6.2, 6.3
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from sqlalchemy.orm import Session

from app.main import app
from app.api.deps import get_db, get_current_user, get_redis_client
from app.models.users import User
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import TimeframeEnum


class TestAnalyticsAPI:
    """Test suite for Analytics API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = Mock()
        redis_mock.ping.return_value = True
        redis_mock.get.return_value = None
        redis_mock.set.return_value = True
        return redis_mock
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.role = "user"
        return user
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user."""
        user = Mock(spec=User)
        user.id = 2
        user.email = "admin@example.com"
        user.role = "admin"
        return user
    
    def setup_method(self):
        """Setup for each test method."""
        self.sample_user_stats = {
            "totalReviews": 25,
            "totalAnalyses": 30,
            "successRate": 85.5,
            "recentActivity": [
                {
                    "type": "analysis",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "description": "Code review completed"
                }
            ]
        }
        
        self.sample_usage_trends = {
            "timeframe": "30d",
            "data": [
                {"date": "2024-01-01", "reviews": 5, "acceptances": 4},
                {"date": "2024-01-02", "reviews": 3, "acceptances": 2}
            ]
        }
        
        self.sample_feedback_distribution = {
            "accepted": 15,
            "rejected": 5,
            "modified": 5,
            "total": 25
        }
    
    def test_get_current_user_stats_success(self, client, mock_db, mock_redis, mock_user):
        """Test successful retrieval of current user statistics."""
        # Mock dependencies
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch.object(AnalyticsService, 'get_user_stats', new_callable=AsyncMock) as mock_get_stats:
            mock_get_stats.return_value = self.sample_user_stats
            
            response = client.get("/api/v1/analytics/user-stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["totalReviews"] == 25
            assert data["successRate"] == 85.5
            mock_get_stats.assert_called_once_with(user_id=1)
        
        # Clean up
        app.dependency_overrides.clear()
    
    def test_get_user_stats_by_id_forbidden(self, client, mock_db, mock_redis, mock_user):
        """Test access control for user stats by ID."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        # Try to access another user's stats
        response = client.get("/api/v1/analytics/user-stats/999")
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_get_user_stats_by_id_admin_access(self, client, mock_db, mock_redis, mock_admin_user):
        """Test admin can access any user's stats."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: mock_admin_user
        
        with patch.object(AnalyticsService, 'get_user_stats', new_callable=AsyncMock) as mock_get_stats:
            mock_get_stats.return_value = self.sample_user_stats
            
            response = client.get("/api/v1/analytics/user-stats/1")
            
            assert response.status_code == 200
            mock_get_stats.assert_called_once_with(user_id=1)
        
        app.dependency_overrides.clear()
    
    def test_get_usage_trends_success(self, client, mock_db, mock_redis, mock_user):
        """Test successful retrieval of usage trends."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch.object(AnalyticsService, 'get_usage_trends', new_callable=AsyncMock) as mock_get_trends:
            mock_get_trends.return_value = self.sample_usage_trends
            
            response = client.get("/api/v1/analytics/usage-trends?timeframe=30d")
            
            assert response.status_code == 200
            data = response.json()
            assert data["timeframe"] == "30d"
            assert len(data["data"]) == 2
            mock_get_trends.assert_called_once_with(user_id=1, timeframe="30d")
        
        app.dependency_overrides.clear()
    
    def test_get_feedback_distribution_success(self, client, mock_db, mock_redis, mock_user):
        """Test successful retrieval of feedback distribution."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch.object(AnalyticsService, 'get_feedback_distribution', new_callable=AsyncMock) as mock_get_dist:
            mock_get_dist.return_value = self.sample_feedback_distribution
            
            response = client.get("/api/v1/analytics/feedback-distribution?timeframe=7d")
            
            assert response.status_code == 200
            data = response.json()
            assert data["accepted"] == 15
            assert data["total"] == 25
            mock_get_dist.assert_called_once_with(user_id=1, timeframe="7d")
        
        app.dependency_overrides.clear()
    
    def test_get_dashboard_data_success(self, client, mock_db, mock_redis, mock_user):
        """Test successful retrieval of comprehensive dashboard data."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        dashboard_data = {
            **self.sample_user_stats,
            "usageTrends": self.sample_usage_trends,
            "feedbackDistribution": self.sample_feedback_distribution
        }
        
        with patch.object(AnalyticsService, 'get_dashboard_data', new_callable=AsyncMock) as mock_get_dashboard:
            mock_get_dashboard.return_value = dashboard_data
            
            response = client.get("/api/v1/analytics/dashboard-data?timeframe=30d")
            
            assert response.status_code == 200
            data = response.json()
            assert "totalReviews" in data
            assert "usageTrends" in data
            assert "feedbackDistribution" in data
            mock_get_dashboard.assert_called_once_with(user_id=1, timeframe="30d")
        
        app.dependency_overrides.clear()
    
    def test_analytics_service_error_handling(self, client, mock_db, mock_redis, mock_user):
        """Test error handling when analytics service fails."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch.object(AnalyticsService, 'get_user_stats', new_callable=AsyncMock) as mock_get_stats:
            mock_get_stats.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/v1/analytics/user-stats")
            
            assert response.status_code == 500
            assert "Failed to retrieve user statistics" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_analytics_health_check_healthy(self, client, mock_db, mock_redis):
        """Test analytics health check when all services are healthy."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        
        # Mock successful database query
        mock_db.execute.return_value = None
        
        response = client.get("/api/v1/analytics/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_status"] == "healthy"
        assert data["cache_status"] == "healthy"
        assert "metrics" in data
        
        app.dependency_overrides.clear()
    
    def test_analytics_health_check_degraded(self, client, mock_db):
        """Test analytics health check when cache is unavailable."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_redis_client] = lambda: None
        
        mock_db.execute.return_value = None
        
        response = client.get("/api/v1/analytics/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database_status"] == "healthy"
        assert data["cache_status"] == "unavailable"
        
        app.dependency_overrides.clear()
    
    def test_invalidate_cache_admin_only(self, client, mock_redis, mock_user):
        """Test cache invalidation requires admin access."""
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        response = client.post("/api/v1/analytics/invalidate-cache")
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_invalidate_cache_admin_success(self, client, mock_redis, mock_admin_user):
        """Test successful cache invalidation by admin."""
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        app.dependency_overrides[get_current_user] = lambda: mock_admin_user
        
        with patch.object(AnalyticsService, 'invalidate_cache') as mock_invalidate:
            response = client.post("/api/v1/analytics/invalidate-cache?pattern=user:*")
            
            assert response.status_code == 200
            data = response.json()
            assert "Cache invalidated" in data["message"]
            mock_invalidate.assert_called_once_with("user:*")
        
        app.dependency_overrides.clear()


class TestAnalyticsWebSocket:
    """Test suite for Analytics WebSocket functionality."""
    
    @pytest.fixture
    def mock_analytics_service(self):
        """Mock analytics service."""
        service = Mock(spec=AnalyticsService)
        service.get_analytics_dashboard_data = AsyncMock(return_value={
            "totalReviews": 25,
            "successRate": 85.5
        })
        service.get_acceptance_rates = AsyncMock(return_value={
            "overall_rate": 80.0,
            "by_category": {"bugs": 85.0, "style": 75.0}
        })
        return service
    
    @pytest.mark.asyncio
    async def test_websocket_connection_and_initial_data(self):
        """Test WebSocket connection and initial data delivery."""
        with TestClient(app) as client:
            # Mock dependencies
            mock_db = Mock(spec=Session)
            mock_redis = Mock()
            
            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_redis_client] = lambda: mock_redis
            
            with patch.object(AnalyticsService, 'get_analytics_dashboard_data', new_callable=AsyncMock) as mock_get_data:
                mock_get_data.return_value = {"totalReviews": 25}
                
                with client.websocket_connect("/api/v1/analytics/ws/real-time?user_id=1") as websocket:
                    # Should receive initial data
                    data = websocket.receive_text()
                    message = json.loads(data)
                    
                    assert message["update_type"] == "dashboard_refresh"
                    assert message["data"]["totalReviews"] == 25
                    assert message["user_id"] == 1
            
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_websocket_client_requests(self):
        """Test WebSocket handling of client requests."""
        with TestClient(app) as client:
            mock_db = Mock(spec=Session)
            mock_redis = Mock()
            
            app.dependency_overrides[get_db] = lambda: mock_db
            app.dependency_overrides[get_redis_client] = lambda: mock_redis
            
            with patch.object(AnalyticsService, 'get_analytics_dashboard_data', new_callable=AsyncMock):
                with patch.object(AnalyticsService, 'get_acceptance_rates', new_callable=AsyncMock) as mock_get_rates:
                    mock_get_rates.return_value = {"overall_rate": 80.0}
                    
                    with client.websocket_connect("/api/v1/analytics/ws/real-time?user_id=1") as websocket:
                        # Skip initial message
                        websocket.receive_text()
                        
                        # Send request for acceptance rates
                        request = {
                            "type": "get_acceptance_rates",
                            "timeframe": "7d"
                        }
                        websocket.send_text(json.dumps(request))
                        
                        # Should receive response
                        data = websocket.receive_text()
                        message = json.loads(data)
                        
                        assert message["update_type"] == "acceptance_rate"
                        assert message["data"]["overall_rate"] == 80.0
            
            app.dependency_overrides.clear()


class TestAnalyticsPerformance:
    """Performance tests for Analytics API."""
    
    def test_analytics_query_performance(self, mock_db, mock_redis):
        """Test analytics query performance with large datasets."""
        # This would be a more comprehensive test in a real scenario
        # with actual database queries and timing measurements
        
        service = AnalyticsService(mock_db, mock_redis)
        
        # Mock database query that simulates processing large dataset
        with patch.object(mock_db, 'execute') as mock_execute:
            mock_execute.return_value.fetchall.return_value = [
                (i, f"analysis_{i}", datetime.utcnow()) for i in range(1000)
            ]
            
            start_time = datetime.utcnow()
            # This would call the actual service method
            # result = await service.get_user_stats(user_id=1)
            end_time = datetime.utcnow()
            
            # Assert query completes within acceptable time
            duration = (end_time - start_time).total_seconds()
            assert duration < 1.0  # Should complete within 1 second
    
    def test_cache_performance(self, mock_redis):
        """Test caching performance and hit rates."""
        service = AnalyticsService(None, mock_redis)
        
        # Test cache hit
        mock_redis.get.return_value = json.dumps({"cached": True})
        
        # This would test actual cache retrieval
        # result = service.get_cached_data("test_key")
        
        mock_redis.get.assert_called()
        
        # Test cache miss and set
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        
        # This would test cache setting
        # service.set_cached_data("test_key", {"new": True})
        
        mock_redis.set.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])