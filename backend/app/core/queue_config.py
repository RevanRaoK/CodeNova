"""
Redis queue configuration and settings for the CodeNova application.

This module provides centralized configuration for:
- Redis queue settings
- Task routing and priority settings
- Monitoring and health check configuration
- Worker configuration

Requirements covered: 5.1, 5.3, 5.5
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class QueuePriority(Enum):
    """Queue priority levels."""
    HIGH = "high_priority"
    MEDIUM = "medium_priority"
    LOW = "low_priority"
    DEFAULT = "default"


@dataclass
class RedisQueueConfig:
    """Configuration class for Redis queue system settings."""
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_DB_QUEUE: int = int(os.getenv("REDIS_DB_QUEUE", "1"))  # Separate DB for queues
    REDIS_DB_RESULTS: int = int(os.getenv("REDIS_DB_RESULTS", "2"))  # Separate DB for results
    
    # Queue Configuration
    QUEUE_PREFIX: str = "codenova:queue:"
    RESULT_PREFIX: str = "codenova:result:"
    PROCESSING_PREFIX: str = "codenova:processing:"
    FAILED_PREFIX: str = "codenova:failed:"
    
    # Task Configuration
    TASK_TIMEOUT: int = int(os.getenv("TASK_TIMEOUT", "600"))  # 10 minutes
    TASK_RETRY_DELAY: int = int(os.getenv("TASK_RETRY_DELAY", "60"))  # 1 minute
    TASK_MAX_RETRIES: int = int(os.getenv("TASK_MAX_RETRIES", "3"))
    RESULT_TTL: int = int(os.getenv("RESULT_TTL", "3600"))  # 1 hour
    
    # Worker Configuration
    WORKER_CONCURRENCY: int = int(os.getenv("WORKER_CONCURRENCY", "4"))
    WORKER_POLL_INTERVAL: float = float(os.getenv("WORKER_POLL_INTERVAL", "1.0"))  # seconds
    WORKER_BATCH_SIZE: int = int(os.getenv("WORKER_BATCH_SIZE", "10"))
    WORKER_MAX_MEMORY_MB: int = int(os.getenv("WORKER_MAX_MEMORY_MB", "512"))
    
    # Performance Configuration
    ENABLE_COMPRESSION: bool = os.getenv("ENABLE_COMPRESSION", "true").lower() == "true"
    ENABLE_PERSISTENCE: bool = os.getenv("ENABLE_PERSISTENCE", "true").lower() == "true"
    BATCH_PROCESSING: bool = os.getenv("BATCH_PROCESSING", "false").lower() == "true"
    
    def get_queue_name(self, priority: QueuePriority) -> str:
        """Get Redis queue name for given priority."""
        return f"{self.QUEUE_PREFIX}{priority.value}"
    
    def get_result_key(self, task_id: str) -> str:
        """Get Redis key for task result."""
        return f"{self.RESULT_PREFIX}{task_id}"
    
    def get_processing_key(self, task_id: str) -> str:
        """Get Redis key for processing task."""
        return f"{self.PROCESSING_PREFIX}{task_id}"
    
    def get_failed_key(self, task_id: str) -> str:
        """Get Redis key for failed task."""
        return f"{self.FAILED_PREFIX}{task_id}"
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration dictionary."""
        return {
            'url': self.REDIS_URL,
            'queue_db': self.REDIS_DB_QUEUE,
            'result_db': self.REDIS_DB_RESULTS,
            'prefixes': {
                'queue': self.QUEUE_PREFIX,
                'result': self.RESULT_PREFIX,
                'processing': self.PROCESSING_PREFIX,
                'failed': self.FAILED_PREFIX,
            },
            'timeouts': {
                'task': self.TASK_TIMEOUT,
                'retry_delay': self.TASK_RETRY_DELAY,
                'result_ttl': self.RESULT_TTL,
            },
            'worker': {
                'concurrency': self.WORKER_CONCURRENCY,
                'poll_interval': self.WORKER_POLL_INTERVAL,
                'batch_size': self.WORKER_BATCH_SIZE,
                'max_memory_mb': self.WORKER_MAX_MEMORY_MB,
            },
            'features': {
                'compression': self.ENABLE_COMPRESSION,
                'persistence': self.ENABLE_PERSISTENCE,
                'batch_processing': self.BATCH_PROCESSING,
            }
        }


@dataclass
class TaskRouting:
    """Task routing configuration for different task types."""
    
    # Task to queue mapping
    TASK_ROUTES: Dict[str, QueuePriority] = None
    
    def __post_init__(self):
        """Initialize task routing after dataclass creation."""
        if self.TASK_ROUTES is None:
            self.TASK_ROUTES = {
                # High priority tasks
                'github_webhook_tasks': QueuePriority.HIGH,
                'urgent_feedback_tasks': QueuePriority.HIGH,
                'real_time_analysis': QueuePriority.HIGH,
                
                # Medium priority tasks
                'file_analysis_tasks': QueuePriority.MEDIUM,
                'feedback_tasks': QueuePriority.MEDIUM,
                'user_requests': QueuePriority.MEDIUM,
                
                # Low priority tasks
                'analytics_tasks': QueuePriority.LOW,
                'cache_tasks': QueuePriority.LOW,
                'cleanup_tasks': QueuePriority.LOW,
                'scheduled_tasks': QueuePriority.LOW,
            }
    
    def get_queue_for_task(self, task_type: str) -> QueuePriority:
        """Get queue priority for given task type."""
        return self.TASK_ROUTES.get(task_type, QueuePriority.DEFAULT)
    
    def get_all_queues(self) -> List[QueuePriority]:
        """Get all available queue priorities."""
        return list(QueuePriority)


@dataclass
class CacheConfig:
    """Configuration for Redis cache system."""
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_DB_CACHE: int = int(os.getenv("REDIS_DB_CACHE", "0"))  # Cache DB
    
    # Cache Configuration
    CACHE_PREFIX: str = "codenova:cache:"
    DEFAULT_CACHE_TTL: int = int(os.getenv("DEFAULT_CACHE_TTL", "3600"))  # 1 hour
    
    # Cache Types and TTLs
    CACHE_TYPES: Dict[str, int] = None
    
    # Performance Settings
    CACHE_HIT_RATE_THRESHOLD: float = float(os.getenv("CACHE_HIT_RATE_THRESHOLD", "0.8"))  # 80%
    CACHE_RESPONSE_TIME_THRESHOLD: int = int(os.getenv("CACHE_RESPONSE_TIME_THRESHOLD", "100"))  # 100ms
    
    # Features
    CACHE_WARMING_ENABLED: bool = os.getenv("CACHE_WARMING_ENABLED", "true").lower() == "true"
    CACHE_INVALIDATION_ENABLED: bool = os.getenv("CACHE_INVALIDATION_ENABLED", "true").lower() == "true"
    CACHE_COMPRESSION_ENABLED: bool = os.getenv("CACHE_COMPRESSION_ENABLED", "false").lower() == "true"
    
    def __post_init__(self):
        """Initialize cache types after dataclass creation."""
        if self.CACHE_TYPES is None:
            self.CACHE_TYPES = {
                'default': self.DEFAULT_CACHE_TTL,
                'user': 1800,      # 30 minutes
                'session': 3600,   # 1 hour
                'file': 7200,      # 2 hours
                'analytics': 900,  # 15 minutes
                'temporary': 300,  # 5 minutes
            }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration for cache."""
        return {
            'url': self.REDIS_URL,
            'db': self.REDIS_DB_CACHE,
            'prefix': self.CACHE_PREFIX,
            'default_ttl': self.DEFAULT_CACHE_TTL,
            'cache_types': self.CACHE_TYPES,
        }
    
    def get_cache_key(self, cache_type: str, key: str) -> str:
        """Get full cache key with prefix and type."""
        return f"{self.CACHE_PREFIX}{cache_type}:{key}"
    
    def get_cache_ttl(self, cache_type: str) -> int:
        """Get TTL for cache type."""
        return self.CACHE_TYPES.get(cache_type, self.DEFAULT_CACHE_TTL)


@dataclass
class MonitoringConfig:
    """Configuration for queue monitoring and health checks."""
    
    # Monitoring Settings
    MONITORING_ENABLED: bool = os.getenv("QUEUE_MONITORING_ENABLED", "true").lower() == "true"
    METRICS_RETENTION_HOURS: int = int(os.getenv("QUEUE_METRICS_RETENTION_HOURS", "24"))
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("QUEUE_HEALTH_CHECK_INTERVAL", "60"))  # seconds
    
    # Alerting Settings
    ALERTING_ENABLED: bool = os.getenv("QUEUE_ALERTING_ENABLED", "false").lower() == "true"
    ALERT_QUEUE_DEPTH_THRESHOLD: int = int(os.getenv("ALERT_QUEUE_DEPTH_THRESHOLD", "1000"))
    ALERT_WORKER_FAILURE_THRESHOLD: int = int(os.getenv("ALERT_WORKER_FAILURE_THRESHOLD", "5"))
    ALERT_TASK_FAILURE_RATE_THRESHOLD: float = float(os.getenv("ALERT_TASK_FAILURE_RATE_THRESHOLD", "0.1"))  # 10%
    
    # Performance Monitoring
    SLOW_TASK_THRESHOLD: int = int(os.getenv("SLOW_TASK_THRESHOLD", "300"))  # 5 minutes
    MEMORY_USAGE_THRESHOLD: float = float(os.getenv("MEMORY_USAGE_THRESHOLD", "0.8"))  # 80%
    CPU_USAGE_THRESHOLD: float = float(os.getenv("CPU_USAGE_THRESHOLD", "0.9"))  # 90%
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("QUEUE_LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = os.getenv("QUEUE_LOG_FILE")
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration dictionary."""
        return {
            'enabled': self.MONITORING_ENABLED,
            'metrics_retention_hours': self.METRICS_RETENTION_HOURS,
            'health_check_interval': self.HEALTH_CHECK_INTERVAL,
            'alerting_enabled': self.ALERTING_ENABLED,
            'thresholds': {
                'queue_depth': self.ALERT_QUEUE_DEPTH_THRESHOLD,
                'worker_failures': self.ALERT_WORKER_FAILURE_THRESHOLD,
                'task_failure_rate': self.ALERT_TASK_FAILURE_RATE_THRESHOLD,
                'slow_task': self.SLOW_TASK_THRESHOLD,
                'memory_usage': self.MEMORY_USAGE_THRESHOLD,
                'cpu_usage': self.CPU_USAGE_THRESHOLD,
            },
            'logging': {
                'level': self.LOG_LEVEL,
                'format': self.LOG_FORMAT,
                'file': self.LOG_FILE,
            }
        }


# Global configuration instances
queue_config = RedisQueueConfig()
task_routing = TaskRouting()
cache_config = CacheConfig()
monitoring_config = MonitoringConfig()


def get_queue_status_summary() -> Dict[str, Any]:
    """Get a summary of queue configuration and status."""
    return {
        'configuration': queue_config.get_redis_config(),
        'monitoring': monitoring_config.get_monitoring_config(),
        'queues': [priority.value for priority in QueuePriority],
        'task_routing': task_routing.TASK_ROUTES,
        'task_modules': [
            'app.tasks.file_analysis_tasks',
            'app.tasks.github_webhook_tasks',
            'app.tasks.feedback_tasks',
            'app.tasks.analytics_tasks',
            'app.tasks.cache_tasks',
        ]
    }


def validate_queue_config() -> Dict[str, Any]:
    """Validate queue configuration settings."""
    issues = []
    warnings = []
    
    # Check Redis URL
    if not queue_config.REDIS_URL:
        issues.append("REDIS_URL is not configured")
    elif not queue_config.REDIS_URL.startswith('redis://'):
        issues.append("REDIS_URL must start with redis://")
    
    # Check worker settings
    if queue_config.WORKER_CONCURRENCY < 1:
        issues.append("WORKER_CONCURRENCY must be at least 1")
    elif queue_config.WORKER_CONCURRENCY > 16:
        warnings.append("High worker concurrency may impact performance")
    
    # Check timeouts
    if queue_config.TASK_TIMEOUT < 60:
        warnings.append("TASK_TIMEOUT is very low, may cause premature timeouts")
    
    # Check memory limits
    if queue_config.WORKER_MAX_MEMORY_MB < 128:
        warnings.append("WORKER_MAX_MEMORY_MB is very low, may cause memory issues")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'configuration_summary': get_queue_status_summary()
    }