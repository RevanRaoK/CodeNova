"""
Logging Configuration Settings

This module provides configuration settings for the enhanced logging system.
"""

import os
from typing import Dict, Any
from app.core.enhanced_logging import ErrorSeverity


class LoggingSettings:
    """Centralized logging configuration settings."""
    
    # Basic logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'structured')  # 'structured' or 'standard'
    
    # File logging settings
    ENABLE_FILE_LOGGING = os.getenv('ENABLE_FILE_LOGGING', 'true').lower() == 'true'
    LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '30'))
    MAX_LOG_FILE_SIZE_MB = int(os.getenv('MAX_LOG_FILE_SIZE_MB', '10'))
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Performance monitoring
    ENABLE_PERFORMANCE_MONITORING = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
    PERFORMANCE_LOG_THRESHOLD_MS = int(os.getenv('PERFORMANCE_LOG_THRESHOLD_MS', '1000'))
    
    # Alert thresholds for different error severities
    ALERT_THRESHOLDS: Dict[ErrorSeverity, int] = {
        ErrorSeverity.LOW: int(os.getenv('ALERT_THRESHOLD_LOW', '50')),
        ErrorSeverity.MEDIUM: int(os.getenv('ALERT_THRESHOLD_MEDIUM', '20')),
        ErrorSeverity.HIGH: int(os.getenv('ALERT_THRESHOLD_HIGH', '5')),
        ErrorSeverity.CRITICAL: int(os.getenv('ALERT_THRESHOLD_CRITICAL', '1'))
    }
    
    # Integration-specific settings
    GITHUB_API_LOG_REQUESTS = os.getenv('GITHUB_API_LOG_REQUESTS', 'false').lower() == 'true'
    FILE_STORAGE_LOG_OPERATIONS = os.getenv('FILE_STORAGE_LOG_OPERATIONS', 'true').lower() == 'true'
    JOB_QUEUE_LOG_PROCESSING = os.getenv('JOB_QUEUE_LOG_PROCESSING', 'true').lower() == 'true'
    
    # Health check logging
    HEALTH_CHECK_LOG_INTERVAL_MINUTES = int(os.getenv('HEALTH_CHECK_LOG_INTERVAL_MINUTES', '5'))
    HEALTH_CHECK_LOG_FAILURES_ONLY = os.getenv('HEALTH_CHECK_LOG_FAILURES_ONLY', 'false').lower() == 'true'
    
    # Error tracking and analysis
    ERROR_PATTERN_ANALYSIS_ENABLED = os.getenv('ERROR_PATTERN_ANALYSIS_ENABLED', 'true').lower() == 'true'
    ERROR_PATTERN_ANALYSIS_WINDOW_HOURS = int(os.getenv('ERROR_PATTERN_ANALYSIS_WINDOW_HOURS', '24'))
    
    # Sensitive data filtering
    SENSITIVE_FIELDS = [
        'password', 'token', 'secret', 'key', 'authorization',
        'access_token', 'refresh_token', 'client_secret', 'api_key'
    ]
    
    @classmethod
    def get_log_config(cls) -> Dict[str, Any]:
        """Get complete logging configuration as dictionary."""
        return {
            'log_level': cls.LOG_LEVEL,
            'log_format': cls.LOG_FORMAT,
            'enable_file_logging': cls.ENABLE_FILE_LOGGING,
            'log_retention_days': cls.LOG_RETENTION_DAYS,
            'max_log_file_size_mb': cls.MAX_LOG_FILE_SIZE_MB,
            'log_backup_count': cls.LOG_BACKUP_COUNT,
            'enable_performance_monitoring': cls.ENABLE_PERFORMANCE_MONITORING,
            'performance_log_threshold_ms': cls.PERFORMANCE_LOG_THRESHOLD_MS,
            'alert_thresholds': cls.ALERT_THRESHOLDS,
            'github_api_log_requests': cls.GITHUB_API_LOG_REQUESTS,
            'file_storage_log_operations': cls.FILE_STORAGE_LOG_OPERATIONS,
            'job_queue_log_processing': cls.JOB_QUEUE_LOG_PROCESSING,
            'health_check_log_interval_minutes': cls.HEALTH_CHECK_LOG_INTERVAL_MINUTES,
            'health_check_log_failures_only': cls.HEALTH_CHECK_LOG_FAILURES_ONLY,
            'error_pattern_analysis_enabled': cls.ERROR_PATTERN_ANALYSIS_ENABLED,
            'error_pattern_analysis_window_hours': cls.ERROR_PATTERN_ANALYSIS_WINDOW_HOURS,
            'sensitive_fields': cls.SENSITIVE_FIELDS
        }
    
    @classmethod
    def is_sensitive_field(cls, field_name: str) -> bool:
        """Check if a field name contains sensitive data."""
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in cls.SENSITIVE_FIELDS)


# Environment-specific configurations
class DevelopmentLoggingSettings(LoggingSettings):
    """Development environment logging settings."""
    LOG_LEVEL = 'DEBUG'
    GITHUB_API_LOG_REQUESTS = True
    PERFORMANCE_LOG_THRESHOLD_MS = 500


class ProductionLoggingSettings(LoggingSettings):
    """Production environment logging settings."""
    LOG_LEVEL = 'INFO'
    LOG_RETENTION_DAYS = 90
    GITHUB_API_LOG_REQUESTS = False
    PERFORMANCE_LOG_THRESHOLD_MS = 2000


class TestingLoggingSettings(LoggingSettings):
    """Testing environment logging settings."""
    LOG_LEVEL = 'WARNING'
    ENABLE_FILE_LOGGING = False
    ENABLE_PERFORMANCE_MONITORING = False


def get_logging_settings() -> LoggingSettings:
    """Get logging settings based on environment."""
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    if environment == 'production':
        return ProductionLoggingSettings()
    elif environment == 'testing':
        return TestingLoggingSettings()
    else:
        return DevelopmentLoggingSettings()