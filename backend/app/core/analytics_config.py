"""
Configuration settings for analytics service.

This module contains configuration constants and settings for:
- Cache TTL values
- Performance thresholds
- Alert thresholds
- WebSocket settings
- Background task intervals

Requirements covered: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from typing import Dict, Any
import os


class AnalyticsConfig:
    """Configuration class for analytics service settings."""
    
    # Cache settings
    DEFAULT_CACHE_TTL = int(os.getenv("ANALYTICS_CACHE_TTL", "300"))  # 5 minutes
    LEARNING_PROGRESS_CACHE_TTL = int(os.getenv("LEARNING_PROGRESS_CACHE_TTL", "1800"))  # 30 minutes
    DASHBOARD_CACHE_TTL = int(os.getenv("DASHBOARD_CACHE_TTL", "180"))  # 3 minutes
    
    # Performance thresholds (in milliseconds)
    QUERY_PERFORMANCE_THRESHOLD = int(os.getenv("QUERY_PERFORMANCE_THRESHOLD", "500"))
    CACHE_HIT_PERFORMANCE_THRESHOLD = int(os.getenv("CACHE_HIT_PERFORMANCE_THRESHOLD", "50"))
    WEBSOCKET_BROADCAST_THRESHOLD = int(os.getenv("WEBSOCKET_BROADCAST_THRESHOLD", "200"))
    
    # Alert thresholds
    LOW_ACCEPTANCE_RATE_THRESHOLD = float(os.getenv("LOW_ACCEPTANCE_RATE_THRESHOLD", "50.0"))
    HIGH_REJECTION_COUNT_THRESHOLD = int(os.getenv("HIGH_REJECTION_COUNT_THRESHOLD", "100"))
    SPECIFIC_REJECTION_REASON_THRESHOLD = int(os.getenv("SPECIFIC_REJECTION_REASON_THRESHOLD", "50"))
    
    # Background task intervals (in seconds)
    CACHE_REFRESH_INTERVAL = int(os.getenv("CACHE_REFRESH_INTERVAL", "300"))  # 5 minutes
    ANALYTICS_BROADCAST_INTERVAL = int(os.getenv("ANALYTICS_BROADCAST_INTERVAL", "30"))  # 30 seconds
    HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "120"))  # 2 minutes
    ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", "600"))  # 10 minutes
    
    # WebSocket settings
    WEBSOCKET_HEARTBEAT_INTERVAL = int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", "30"))  # 30 seconds
    MAX_WEBSOCKET_CONNECTIONS = int(os.getenv("MAX_WEBSOCKET_CONNECTIONS", "1000"))
    WEBSOCKET_MESSAGE_TIMEOUT = int(os.getenv("WEBSOCKET_MESSAGE_TIMEOUT", "30"))
    
    # Data export settings
    MAX_EXPORT_RECORDS = int(os.getenv("MAX_EXPORT_RECORDS", "10000"))
    EXPORT_TIMEOUT_SECONDS = int(os.getenv("EXPORT_TIMEOUT_SECONDS", "300"))  # 5 minutes
    
    # Analytics data retention
    ANALYTICS_DATA_RETENTION_DAYS = int(os.getenv("ANALYTICS_DATA_RETENTION_DAYS", "365"))  # 1 year
    CACHE_CLEANUP_INTERVAL = int(os.getenv("CACHE_CLEANUP_INTERVAL", "3600"))  # 1 hour
    
    # Redis settings
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "analytics")
    REDIS_CONNECTION_TIMEOUT = int(os.getenv("REDIS_CONNECTION_TIMEOUT", "5"))
    
    # Database query optimization
    QUERY_BATCH_SIZE = int(os.getenv("QUERY_BATCH_SIZE", "1000"))
    MAX_CONCURRENT_QUERIES = int(os.getenv("MAX_CONCURRENT_QUERIES", "10"))
    
    @classmethod
    def get_cache_ttl(cls, cache_type: str) -> int:
        """Get cache TTL for specific cache type."""
        ttl_map = {
            "default": cls.DEFAULT_CACHE_TTL,
            "learning_progress": cls.LEARNING_PROGRESS_CACHE_TTL,
            "dashboard": cls.DASHBOARD_CACHE_TTL,
        }
        return ttl_map.get(cache_type, cls.DEFAULT_CACHE_TTL)
    
    @classmethod
    def get_performance_threshold(cls, operation: str) -> int:
        """Get performance threshold for specific operation."""
        threshold_map = {
            "query": cls.QUERY_PERFORMANCE_THRESHOLD,
            "cache_hit": cls.CACHE_HIT_PERFORMANCE_THRESHOLD,
            "websocket_broadcast": cls.WEBSOCKET_BROADCAST_THRESHOLD,
        }
        return threshold_map.get(operation, cls.QUERY_PERFORMANCE_THRESHOLD)
    
    @classmethod
    def get_alert_threshold(cls, alert_type: str) -> float:
        """Get alert threshold for specific alert type."""
        threshold_map = {
            "low_acceptance_rate": cls.LOW_ACCEPTANCE_RATE_THRESHOLD,
            "high_rejection_count": cls.HIGH_REJECTION_COUNT_THRESHOLD,
            "specific_rejection_reason": cls.SPECIFIC_REJECTION_REASON_THRESHOLD,
        }
        return threshold_map.get(alert_type, 0.0)
    
    @classmethod
    def get_task_interval(cls, task_type: str) -> int:
        """Get interval for specific background task type."""
        interval_map = {
            "cache_refresh": cls.CACHE_REFRESH_INTERVAL,
            "analytics_broadcast": cls.ANALYTICS_BROADCAST_INTERVAL,
            "health_check": cls.HEALTH_CHECK_INTERVAL,
            "alert_check": cls.ALERT_CHECK_INTERVAL,
        }
        return interval_map.get(task_type, cls.CACHE_REFRESH_INTERVAL)
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Get Redis configuration dictionary."""
        return {
            "url": cls.REDIS_URL,
            "key_prefix": cls.REDIS_KEY_PREFIX,
            "connection_timeout": cls.REDIS_CONNECTION_TIMEOUT,
            "decode_responses": True,
        }
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validate configuration settings and return validation results."""
        validation_results = {}
        
        # Validate cache TTL values
        validation_results["cache_ttl_valid"] = cls.DEFAULT_CACHE_TTL > 0
        validation_results["learning_cache_ttl_valid"] = cls.LEARNING_PROGRESS_CACHE_TTL > 0
        
        # Validate performance thresholds
        validation_results["query_threshold_valid"] = cls.QUERY_PERFORMANCE_THRESHOLD > 0
        validation_results["cache_threshold_valid"] = cls.CACHE_HIT_PERFORMANCE_THRESHOLD > 0
        
        # Validate alert thresholds
        validation_results["acceptance_threshold_valid"] = 0 <= cls.LOW_ACCEPTANCE_RATE_THRESHOLD <= 100
        validation_results["rejection_threshold_valid"] = cls.HIGH_REJECTION_COUNT_THRESHOLD > 0
        
        # Validate intervals
        validation_results["refresh_interval_valid"] = cls.CACHE_REFRESH_INTERVAL > 0
        validation_results["broadcast_interval_valid"] = cls.ANALYTICS_BROADCAST_INTERVAL > 0
        
        # Validate WebSocket settings
        validation_results["websocket_connections_valid"] = cls.MAX_WEBSOCKET_CONNECTIONS > 0
        validation_results["websocket_timeout_valid"] = cls.WEBSOCKET_MESSAGE_TIMEOUT > 0
        
        return validation_results
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Get a summary of current configuration settings."""
        return {
            "cache_settings": {
                "default_ttl": cls.DEFAULT_CACHE_TTL,
                "learning_progress_ttl": cls.LEARNING_PROGRESS_CACHE_TTL,
                "dashboard_ttl": cls.DASHBOARD_CACHE_TTL,
            },
            "performance_thresholds": {
                "query_threshold_ms": cls.QUERY_PERFORMANCE_THRESHOLD,
                "cache_hit_threshold_ms": cls.CACHE_HIT_PERFORMANCE_THRESHOLD,
                "websocket_broadcast_threshold_ms": cls.WEBSOCKET_BROADCAST_THRESHOLD,
            },
            "alert_thresholds": {
                "low_acceptance_rate": cls.LOW_ACCEPTANCE_RATE_THRESHOLD,
                "high_rejection_count": cls.HIGH_REJECTION_COUNT_THRESHOLD,
                "specific_rejection_reason": cls.SPECIFIC_REJECTION_REASON_THRESHOLD,
            },
            "task_intervals": {
                "cache_refresh_seconds": cls.CACHE_REFRESH_INTERVAL,
                "analytics_broadcast_seconds": cls.ANALYTICS_BROADCAST_INTERVAL,
                "health_check_seconds": cls.HEALTH_CHECK_INTERVAL,
                "alert_check_seconds": cls.ALERT_CHECK_INTERVAL,
            },
            "websocket_settings": {
                "heartbeat_interval": cls.WEBSOCKET_HEARTBEAT_INTERVAL,
                "max_connections": cls.MAX_WEBSOCKET_CONNECTIONS,
                "message_timeout": cls.WEBSOCKET_MESSAGE_TIMEOUT,
            },
            "redis_settings": {
                "url": cls.REDIS_URL,
                "key_prefix": cls.REDIS_KEY_PREFIX,
                "connection_timeout": cls.REDIS_CONNECTION_TIMEOUT,
            }
        }


# Global configuration instance
analytics_config = AnalyticsConfig()