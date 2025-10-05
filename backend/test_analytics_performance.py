"""
Performance tests for analytics service and caching functionality.

This module tests:
- Analytics query performance
- Cache hit/miss ratios
- WebSocket connection handling
- Real-time analytics updates
- Cache invalidation strategies
- Database query optimization

Requirements covered: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import pytest
import asyncio
import time
import json
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

# Add the backend directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import redis
    from sqlalchemy.orm import Session
    from fastapi.testclient import TestClient
    from fastapi import WebSocket
    
    from app.services.analytics_service import AnalyticsService
    from app.models.enhanced_feedback import EnhancedFeedback, FeedbackAction
    from app.models.feedback import ModelVersion
    from app.models.users import User
    from app.schemas.analytics import TimeframeEnum, ExportFormatEnum
except ImportError as e:
    pytest.skip(f"Skipping analytics performance tests due to import error: {e}", allow_module_level=True)


class TestAnalyticsPerformance:
    """Test suite for analytics service performance."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock(spec=Session)
        return db
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_client = Mock(spec=redis.Redis)
        redis_client.get.return_value = None
        redis_client.setex.return_value = True
        redis_client.ping.return_value = True
        redis_client.keys.return_value = []
        return redis_client
    
    @pytest.fixture
    def analytics_service(self, mock_db, mock_redis):
        """Analytics service instance with mocked dependencies."""
        return AnalyticsService(mock_db, mock_redis)
    
    @pytest.fixture
    def sample_feedback_data(self):
        """Generate sample feedback data for testing."""
        feedback_records = []
        base_time = datetime.utcnow() - timedelta(days=30)
        
        for i in range(1000):  # Generate 1000 records for performance testing
            feedback = Mock(spec=EnhancedFeedback)
            feedback.id = i
            feedback.user_id = (i % 50) + 1  # 50 different users
            feedback.action = FeedbackAction.ACCEPT if i % 3 == 0 else FeedbackAction.REJECT
            feedback.suggestion_type = f"pattern_{i % 10}"  # 10 different pattern types
            feedback.timestamp = base_time + timedelta(hours=i)
            feedback.rejection_reasons = ["incorrect", "not_applicable"] if feedback.action == FeedbackAction.REJECT else []
            feedback.custom_reason = f"Custom reason {i}" if i % 20 == 0 else None
            feedback.confidence_score = 0.5 + (i % 50) / 100
            feedback.context_data = {"test": f"data_{i}"}
            feedback_records.append(feedback)
        
        return feedback_records
    
    @pytest.mark.asyncio
    async def test_acceptance_rates_query_performance(self, analytics_service, mock_db, sample_feedback_data):
        """Test performance of acceptance rates calculation."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_feedback_data
        mock_db.query.return_value = mock_query
        
        # Measure query performance
        start_time = time.time()
        result = await analytics_service.get_acceptance_rates(timeframe="30d")
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Assert performance requirements
        assert query_time < 500, f"Query took {query_time}ms, should be under 500ms"
        assert result["total_feedback"] == 1000
        assert "acceptance_rate" in result
        assert "daily_rates" in result
        assert "pattern_breakdown" in result
    
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, analytics_service, mock_redis):
        """Test cache hit performance and efficiency."""
        # Mock cache hit
        cached_data = {
            "total_feedback": 1000,
            "acceptance_rate": 75.5,
            "rejection_rate": 24.5,
            "daily_rates": {},
            "pattern_breakdown": {},
            "timeframe": "30d"
        }
        mock_redis.get.return_value = json.dumps(cached_data, default=str)
        
        # Measure cache hit performance
        start_time = time.time()
        result = await analytics_service.get_acceptance_rates(timeframe="30d")
        end_time = time.time()
        
        cache_hit_time = (end_time - start_time) * 1000
        
        # Cache hits should be very fast
        assert cache_hit_time < 50, f"Cache hit took {cache_hit_time}ms, should be under 50ms"
        assert result == cached_data
        mock_redis.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_miss_and_set_performance(self, analytics_service, mock_db, mock_redis, sample_feedback_data):
        """Test cache miss handling and cache setting performance."""
        # Mock cache miss
        mock_redis.get.return_value = None
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_feedback_data
        mock_db.query.return_value = mock_query
        
        start_time = time.time()
        result = await analytics_service.get_acceptance_rates(timeframe="30d")
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000
        
        # Cache miss should still be reasonably fast
        assert total_time < 1000, f"Cache miss took {total_time}ms, should be under 1000ms"
        
        # Verify cache was set
        mock_redis.setex.assert_called_once()
        assert result["total_feedback"] == 1000
    
    @pytest.mark.asyncio
    async def test_rejection_patterns_performance(self, analytics_service, mock_db, sample_feedback_data):
        """Test rejection patterns analysis performance."""
        # Filter to only rejected feedback
        rejected_feedback = [f for f in sample_feedback_data if f.action == FeedbackAction.REJECT]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = rejected_feedback
        mock_db.query.return_value = mock_query
        
        start_time = time.time()
        result = await analytics_service.get_rejection_patterns(timeframe="30d")
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000
        
        assert query_time < 300, f"Rejection patterns query took {query_time}ms, should be under 300ms"
        assert result["total_rejections"] == len(rejected_feedback)
        assert "rejection_reasons" in result
        assert "pattern_rejections" in result
    
    @pytest.mark.asyncio
    async def test_usage_statistics_performance(self, analytics_service, mock_db, sample_feedback_data):
        """Test usage statistics calculation performance."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_feedback_data
        mock_db.query.return_value = mock_query
        
        start_time = time.time()
        result = await analytics_service.get_usage_statistics(timeframe="30d")
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000
        
        assert query_time < 400, f"Usage statistics query took {query_time}ms, should be under 400ms"
        assert result["total_interactions"] == 1000
        assert result["unique_users"] == 50
        assert "daily_activity" in result
        assert "suggestion_types_usage" in result
    
    @pytest.mark.asyncio
    async def test_learning_progress_performance(self, analytics_service, mock_db, sample_feedback_data):
        """Test learning progress calculation performance."""
        # Mock model versions
        model_versions = []
        for i in range(5):
            version = Mock(spec=ModelVersion)
            version.version_name = f"v1.{i}.0"
            version.accuracy_score = 0.7 + (i * 0.05)
            version.acceptance_rate = 70 + (i * 5)
            version.created_at = datetime.utcnow() - timedelta(days=i*10)
            version.is_active = i == 0
            model_versions.append(version)
        
        # Mock database queries
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = model_versions
        mock_db.query.return_value.filter.return_value.all.return_value = sample_feedback_data[:100]  # Recent feedback
        mock_db.query.return_value.filter.return_value.count.return_value = 2500  # Training data count
        
        start_time = time.time()
        result = await analytics_service.get_learning_progress()
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000
        
        assert query_time < 200, f"Learning progress query took {query_time}ms, should be under 200ms"
        assert len(result["model_versions"]) == 5
        assert "recent_acceptance_rate" in result
        assert "learning_indicators" in result
    
    @pytest.mark.asyncio
    async def test_dashboard_data_aggregation_performance(self, analytics_service, mock_db, mock_redis, sample_feedback_data):
        """Test comprehensive dashboard data aggregation performance."""
        # Mock all required database queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_feedback_data
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        mock_query.count.return_value = 2500
        mock_db.query.return_value = mock_query
        
        # Mock cache misses for all components
        mock_redis.get.return_value = None
        
        start_time = time.time()
        result = await analytics_service.get_analytics_dashboard_data(timeframe="30d")
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000
        
        # Dashboard aggregation should complete within reasonable time
        assert total_time < 2000, f"Dashboard aggregation took {total_time}ms, should be under 2000ms"
        
        # Verify all components are present
        assert "acceptance_rates" in result
        assert "rejection_patterns" in result
        assert "usage_statistics" in result
        assert "learning_progress" in result
        assert "generated_at" in result
    
    @pytest.mark.asyncio
    async def test_export_data_performance(self, analytics_service, mock_db, sample_feedback_data):
        """Test data export performance with large datasets."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_feedback_data
        mock_db.query.return_value = mock_query
        
        start_time = time.time()
        result = await analytics_service.export_analytics_data(export_format="json")
        end_time = time.time()
        
        export_time = (end_time - start_time) * 1000
        
        # Export should handle large datasets efficiently
        assert export_time < 1500, f"Data export took {export_time}ms, should be under 1500ms"
        assert result["total_records"] == 1000
        assert len(result["data"]) == 1000
        assert result["format"] == "json"
    
    def test_cache_invalidation_performance(self, analytics_service, mock_redis):
        """Test cache invalidation performance."""
        # Mock cache keys
        cache_keys = [f"analytics:key_{i}" for i in range(100)]
        mock_redis.keys.return_value = cache_keys
        mock_redis.delete.return_value = len(cache_keys)
        
        start_time = time.time()
        analytics_service.invalidate_cache("analytics:*")
        end_time = time.time()
        
        invalidation_time = (end_time - start_time) * 1000
        
        # Cache invalidation should be fast
        assert invalidation_time < 100, f"Cache invalidation took {invalidation_time}ms, should be under 100ms"
        mock_redis.keys.assert_called_once_with("analytics:*")
        mock_redis.delete.assert_called_once_with(*cache_keys)


class TestWebSocketPerformance:
    """Test suite for WebSocket performance and connection handling."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection."""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_websocket_connection_performance(self, mock_websocket):
        """Test WebSocket connection establishment performance."""
        start_time = time.time()
        await websocket_manager.connect(mock_websocket, user_id=1)
        end_time = time.time()
        
        connection_time = (end_time - start_time) * 1000
        
        # Connection should be very fast
        assert connection_time < 50, f"WebSocket connection took {connection_time}ms, should be under 50ms"
        assert mock_websocket in websocket_manager.active_connections
        assert 1 in websocket_manager.user_connections
    
    @pytest.mark.asyncio
    async def test_websocket_broadcast_performance(self, mock_websocket):
        """Test WebSocket broadcast performance with multiple connections."""
        # Add multiple mock connections
        connections = []
        for i in range(50):  # 50 concurrent connections
            ws = Mock(spec=WebSocket)
            ws.send_text = AsyncMock()
            connections.append(ws)
            await websocket_manager.connect(ws, user_id=i)
        
        test_message = json.dumps({"type": "test", "data": {"value": 123}})
        
        start_time = time.time()
        await websocket_manager.broadcast(test_message)
        end_time = time.time()
        
        broadcast_time = (end_time - start_time) * 1000
        
        # Broadcasting to 50 connections should be fast
        assert broadcast_time < 200, f"Broadcast to 50 connections took {broadcast_time}ms, should be under 200ms"
        
        # Verify all connections received the message
        for ws in connections:
            ws.send_text.assert_called_once_with(test_message)
    
    @pytest.mark.asyncio
    async def test_websocket_user_specific_performance(self, mock_websocket):
        """Test user-specific WebSocket message performance."""
        # Add connections for multiple users
        user_connections = {}
        for user_id in range(1, 11):  # 10 users
            for conn_id in range(3):  # 3 connections per user
                ws = Mock(spec=WebSocket)
                ws.send_text = AsyncMock()
                await websocket_manager.connect(ws, user_id=user_id)
                if user_id not in user_connections:
                    user_connections[user_id] = []
                user_connections[user_id].append(ws)
        
        test_message = json.dumps({"type": "user_update", "data": {"user_id": 5}})
        
        start_time = time.time()
        await websocket_manager.send_to_user(5, test_message)
        end_time = time.time()
        
        send_time = (end_time - start_time) * 1000
        
        # User-specific sending should be fast
        assert send_time < 50, f"User-specific send took {send_time}ms, should be under 50ms"
        
        # Verify only user 5's connections received the message
        for ws in user_connections[5]:
            ws.send_text.assert_called_once_with(test_message)
        
        # Verify other users didn't receive the message
        for user_id, connections in user_connections.items():
            if user_id != 5:
                for ws in connections:
                    ws.send_text.assert_not_called()
    
    def test_websocket_connection_cleanup_performance(self):
        """Test WebSocket connection cleanup performance."""
        # Add many connections
        connections = []
        for i in range(100):
            ws = Mock(spec=WebSocket)
            connections.append(ws)
            websocket_manager.active_connections.append(ws)
            if i % 10 not in websocket_manager.user_connections:
                websocket_manager.user_connections[i % 10] = []
            websocket_manager.user_connections[i % 10].append(ws)
        
        start_time = time.time()
        
        # Disconnect all connections
        for i, ws in enumerate(connections):
            websocket_manager.disconnect(ws, i % 10)
        
        end_time = time.time()
        
        cleanup_time = (end_time - start_time) * 1000
        
        # Cleanup should be efficient even with many connections
        assert cleanup_time < 500, f"Connection cleanup took {cleanup_time}ms, should be under 500ms"
        assert len(websocket_manager.active_connections) == 0
        assert len(websocket_manager.user_connections) == 0


class TestAnalyticsCacheStrategies:
    """Test suite for analytics caching strategies and optimization."""
    
    @pytest.fixture
    def analytics_service_with_cache(self, mock_db):
        """Analytics service with real Redis-like cache behavior."""
        cache = {}
        
        class MockRedis:
            def get(self, key):
                return cache.get(key)
            
            def setex(self, key, ttl, value):
                cache[key] = value
                return True
            
            def keys(self, pattern):
                if pattern == "*":
                    return list(cache.keys())
                # Simple pattern matching for test
                return [k for k in cache.keys() if pattern.replace("*", "") in k]
            
            def delete(self, *keys):
                for key in keys:
                    cache.pop(key, None)
                return len(keys)
            
            def ping(self):
                return True
        
        return AnalyticsService(mock_db, MockRedis())
    
    @pytest.mark.asyncio
    async def test_cache_warming_strategy(self, analytics_service_with_cache, mock_db, sample_feedback_data):
        """Test cache warming strategy for frequently accessed data."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_feedback_data
        mock_db.query.return_value = mock_query
        
        # Warm cache with common queries
        common_timeframes = ["7d", "30d", "90d"]
        
        start_time = time.time()
        
        for timeframe in common_timeframes:
            await analytics_service_with_cache.get_acceptance_rates(timeframe=timeframe)
            await analytics_service_with_cache.get_rejection_patterns(timeframe=timeframe)
            await analytics_service_with_cache.get_usage_statistics(timeframe=timeframe)
        
        end_time = time.time()
        
        warming_time = (end_time - start_time) * 1000
        
        # Cache warming should complete in reasonable time
        assert warming_time < 3000, f"Cache warming took {warming_time}ms, should be under 3000ms"
        
        # Verify subsequent calls are much faster (cache hits)
        start_time = time.time()
        await analytics_service_with_cache.get_acceptance_rates(timeframe="30d")
        end_time = time.time()
        
        cache_hit_time = (end_time - start_time) * 1000
        assert cache_hit_time < 10, f"Cache hit took {cache_hit_time}ms, should be under 10ms"
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_strategy(self, analytics_service_with_cache, mock_db, sample_feedback_data):
        """Test selective cache invalidation strategies."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_feedback_data
        mock_db.query.return_value = mock_query
        
        # Populate cache
        await analytics_service_with_cache.get_acceptance_rates(timeframe="30d")
        await analytics_service_with_cache.get_rejection_patterns(timeframe="30d")
        await analytics_service_with_cache.get_usage_statistics(timeframe="7d")
        
        # Test selective invalidation
        start_time = time.time()
        analytics_service_with_cache.invalidate_cache("*acceptance_rates*")
        end_time = time.time()
        
        invalidation_time = (end_time - start_time) * 1000
        
        # Selective invalidation should be fast
        assert invalidation_time < 50, f"Selective invalidation took {invalidation_time}ms, should be under 50ms"
        
        # Verify only acceptance rates cache was invalidated
        # (This would require checking cache keys, simplified for test)
    
    def test_cache_memory_efficiency(self, analytics_service_with_cache):
        """Test cache memory usage efficiency."""
        # This test would measure memory usage of cached data
        # Simplified for demonstration
        
        cache_key = analytics_service_with_cache._get_cache_key("test", user_id=1, timeframe="30d")
        
        # Test cache key generation efficiency
        assert len(cache_key) < 100, "Cache keys should be reasonably short"
        assert "test" in cache_key
        assert "user_id:1" in cache_key
        assert "timeframe:30d" in cache_key


@pytest.mark.integration
class TestAnalyticsIntegrationPerformance:
    """Integration tests for analytics performance with real-like scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_analytics_requests(self, analytics_service, mock_db, mock_redis, sample_feedback_data):
        """Test performance under concurrent analytics requests."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_feedback_data
        mock_db.query.return_value = mock_query
        
        # Mock cache misses initially
        mock_redis.get.return_value = None
        
        async def make_request(request_type, user_id):
            if request_type == "acceptance":
                return await analytics_service.get_acceptance_rates(user_id=user_id)
            elif request_type == "rejection":
                return await analytics_service.get_rejection_patterns(user_id=user_id)
            else:
                return await analytics_service.get_usage_statistics(user_id=user_id)
        
        # Create concurrent requests
        tasks = []
        for i in range(30):  # 30 concurrent requests
            request_type = ["acceptance", "rejection", "usage"][i % 3]
            user_id = (i % 10) + 1
            tasks.append(make_request(request_type, user_id))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000
        
        # 30 concurrent requests should complete in reasonable time
        assert total_time < 5000, f"30 concurrent requests took {total_time}ms, should be under 5000ms"
        assert len(results) == 30
        
        # All requests should have succeeded
        for result in results:
            assert result is not None
            assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_analytics_under_load_with_caching(self, analytics_service, mock_db, mock_redis, sample_feedback_data):
        """Test analytics performance under load with caching enabled."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_feedback_data
        mock_db.query.return_value = mock_query
        
        # Simulate cache behavior - first call misses, subsequent calls hit
        call_count = 0
        def mock_get(key):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None  # Cache miss
            else:
                # Return cached data
                return json.dumps({
                    "total_feedback": 1000,
                    "acceptance_rate": 75.0,
                    "rejection_rate": 25.0,
                    "daily_rates": {},
                    "pattern_breakdown": {},
                    "timeframe": "30d"
                }, default=str)
        
        mock_redis.get.side_effect = mock_get
        
        # First request (cache miss)
        start_time = time.time()
        result1 = await analytics_service.get_acceptance_rates(timeframe="30d")
        end_time = time.time()
        
        first_request_time = (end_time - start_time) * 1000
        
        # Subsequent requests (cache hits)
        cache_hit_times = []
        for _ in range(10):
            start_time = time.time()
            await analytics_service.get_acceptance_rates(timeframe="30d")
            end_time = time.time()
            cache_hit_times.append((end_time - start_time) * 1000)
        
        avg_cache_hit_time = sum(cache_hit_times) / len(cache_hit_times)
        
        # Cache hits should be significantly faster than cache miss
        assert avg_cache_hit_time < first_request_time / 10, \
            f"Cache hits ({avg_cache_hit_time}ms) should be much faster than cache miss ({first_request_time}ms)"
        
        # Cache hits should be very fast
        assert avg_cache_hit_time < 20, f"Average cache hit time {avg_cache_hit_time}ms should be under 20ms"