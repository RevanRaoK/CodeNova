"""
Enhanced Logging and Error Handling System

This module provides comprehensive structured logging, error handling, and monitoring
for all integration operations including file storage, GitHub integration, and job queues.

Requirements covered: 5.1, 5.2, 5.4
"""

import logging
import logging.handlers
import json
import traceback
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
from contextlib import contextmanager
import asyncio
import threading
from pathlib import Path

from app.core.config import settings
from app.core.monitoring import ServiceType, StructuredLogger


class ErrorSeverity(str, Enum):
    """Error severity levels for categorization and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IntegrationComponent(str, Enum):
    """Integration components for error categorization."""
    FILE_STORAGE = "file_storage"
    GITHUB_OAUTH = "github_oauth"
    GITHUB_WEBHOOK = "github_webhook"
    GITHUB_API = "github_api"
    JOB_QUEUE = "job_queue"
    BACKGROUND_ANALYSIS = "background_analysis"
    USER_PROFILE = "user_profile"
    CONFIGURATION = "configuration"
    HEALTH_CHECK = "health_check"


@dataclass
class ErrorContext:
    """Structured error context for detailed error reporting."""
    component: IntegrationComponent
    operation: str
    severity: ErrorSeverity
    error_code: str
    error_message: str
    user_id: Optional[int] = None
    request_id: Optional[str] = None
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    traceback_info: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class IntegrationAlert:
    """Alert for integration failures requiring attention."""
    alert_id: str
    component: IntegrationComponent
    severity: ErrorSeverity
    title: str
    description: str
    error_count: int
    first_occurrence: datetime
    last_occurrence: datetime
    affected_users: List[int]
    metadata: Dict[str, Any]


class EnhancedLogger:
    """Enhanced structured logger with integration-specific features."""
    
    def __init__(self, component: IntegrationComponent, name: str = None):
        self.component = component
        self.name = name or f"{component.value}_logger"
        self.logger = logging.getLogger(self.name)
        self._setup_logger()
        self._error_cache = {}
        self._alert_thresholds = {
            ErrorSeverity.LOW: 50,
            ErrorSeverity.MEDIUM: 20,
            ErrorSeverity.HIGH: 5,
            ErrorSeverity.CRITICAL: 1
        }
    
    def _setup_logger(self):
        """Configure logger with appropriate handlers and formatters."""
        if self.logger.handlers:
            return  # Already configured
            
        self.logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        
        # Console handler with structured format
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = StructuredFormatter()
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for persistent logging
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.component.value}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(console_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler for errors only
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.component.value}_errors.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(console_formatter)
        self.logger.addHandler(error_handler)
    
    def log_operation(self, operation: str, level: str = "info", **kwargs):
        """Log an operation with structured context."""
        log_data = {
            "component": self.component.value,
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        getattr(self.logger, level.lower())(
            f"[{self.component.value}] {operation}",
            extra={"structured_data": log_data}
        )
    
    def log_error(self, error_context: ErrorContext):
        """Log an error with full context and tracking."""
        log_data = asdict(error_context)
        log_data["timestamp"] = error_context.timestamp.isoformat()
        
        self.logger.error(
            f"[{error_context.component.value}] {error_context.operation}: {error_context.error_message}",
            extra={"structured_data": log_data}
        )
        
        # Track error for alerting
        self._track_error(error_context)
    
    def _track_error(self, error_context: ErrorContext):
        """Track errors for alerting thresholds."""
        cache_key = f"{error_context.component.value}:{error_context.error_code}"
        
        if cache_key not in self._error_cache:
            self._error_cache[cache_key] = {
                "count": 0,
                "first_occurrence": error_context.timestamp,
                "last_occurrence": error_context.timestamp,
                "severity": error_context.severity,
                "affected_users": set()
            }
        
        cache_entry = self._error_cache[cache_key]
        cache_entry["count"] += 1
        cache_entry["last_occurrence"] = error_context.timestamp
        
        if error_context.user_id:
            cache_entry["affected_users"].add(error_context.user_id)
        
        # Check if alert threshold is reached
        threshold = self._alert_thresholds.get(error_context.severity, 10)
        if cache_entry["count"] >= threshold:
            self._create_alert(error_context, cache_entry)
    
    def _create_alert(self, error_context: ErrorContext, cache_entry: Dict):
        """Create an alert for threshold breach."""
        alert = IntegrationAlert(
            alert_id=f"{error_context.component.value}_{error_context.error_code}_{int(datetime.utcnow().timestamp())}",
            component=error_context.component,
            severity=error_context.severity,
            title=f"{error_context.component.value} Error Threshold Exceeded",
            description=f"Error {error_context.error_code} occurred {cache_entry['count']} times",
            error_count=cache_entry["count"],
            first_occurrence=cache_entry["first_occurrence"],
            last_occurrence=cache_entry["last_occurrence"],
            affected_users=list(cache_entry["affected_users"]),
            metadata={
                "error_code": error_context.error_code,
                "operation": error_context.operation,
                "threshold": self._alert_thresholds.get(error_context.severity, 10)
            }
        )
        
        # Log the alert
        self.logger.critical(
            f"ALERT: {alert.title}",
            extra={"structured_data": asdict(alert)}
        )
        
        # Reset counter after alert
        cache_key = f"{error_context.component.value}:{error_context.error_code}"
        self._error_cache[cache_key]["count"] = 0


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging output."""
    
    def format(self, record):
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add structured data if available
        if hasattr(record, 'structured_data'):
            log_entry.update(record.structured_data)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class IntegrationErrorHandler:
    """Centralized error handling for integration operations."""
    
    def __init__(self):
        self.loggers = {}
        self._setup_global_exception_handler()
    
    def get_logger(self, component: IntegrationComponent) -> EnhancedLogger:
        """Get or create a logger for a specific component."""
        if component not in self.loggers:
            self.loggers[component] = EnhancedLogger(component)
        return self.loggers[component]
    
    def _setup_global_exception_handler(self):
        """Setup global exception handler for uncaught exceptions."""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            error_context = ErrorContext(
                component=IntegrationComponent.CONFIGURATION,
                operation="global_exception_handler",
                severity=ErrorSeverity.CRITICAL,
                error_code="UNCAUGHT_EXCEPTION",
                error_message=str(exc_value),
                traceback_info="".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            )
            
            logger = self.get_logger(IntegrationComponent.CONFIGURATION)
            logger.log_error(error_context)
        
        sys.excepthook = handle_exception


def log_integration_operation(component: IntegrationComponent, operation: str):
    """Decorator for logging integration operations."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = error_handler.get_logger(component)
            start_time = datetime.utcnow()
            
            logger.log_operation(
                operation,
                level="info",
                status="started",
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.log_operation(
                    operation,
                    level="info",
                    status="completed",
                    duration_seconds=duration,
                    function=func.__name__
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                error_context = ErrorContext(
                    component=component,
                    operation=operation,
                    severity=ErrorSeverity.HIGH,
                    error_code=type(e).__name__,
                    error_message=str(e),
                    traceback_info=traceback.format_exc(),
                    metadata={
                        "function": func.__name__,
                        "duration_seconds": duration,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                )
                
                logger.log_error(error_context)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = error_handler.get_logger(component)
            start_time = datetime.utcnow()
            
            logger.log_operation(
                operation,
                level="info",
                status="started",
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.log_operation(
                    operation,
                    level="info",
                    status="completed",
                    duration_seconds=duration,
                    function=func.__name__
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                error_context = ErrorContext(
                    component=component,
                    operation=operation,
                    severity=ErrorSeverity.HIGH,
                    error_code=type(e).__name__,
                    error_message=str(e),
                    traceback_info=traceback.format_exc(),
                    metadata={
                        "function": func.__name__,
                        "duration_seconds": duration,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                )
                
                logger.log_error(error_context)
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


@contextmanager
def log_integration_context(component: IntegrationComponent, operation: str, **context):
    """Context manager for logging integration operations with cleanup."""
    logger = error_handler.get_logger(component)
    start_time = datetime.utcnow()
    
    logger.log_operation(
        operation,
        level="info",
        status="context_entered",
        **context
    )
    
    try:
        yield logger
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.log_operation(
            operation,
            level="info",
            status="context_completed",
            duration_seconds=duration,
            **context
        )
        
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        error_context = ErrorContext(
            component=component,
            operation=operation,
            severity=ErrorSeverity.HIGH,
            error_code=type(e).__name__,
            error_message=str(e),
            traceback_info=traceback.format_exc(),
            metadata={
                "duration_seconds": duration,
                **context
            }
        )
        
        logger.log_error(error_context)
        raise


class PerformanceMonitor:
    """Monitor performance metrics for integration operations."""
    
    def __init__(self):
        self.metrics = {}
        self.logger = error_handler.get_logger(IntegrationComponent.CONFIGURATION)
    
    def record_operation(self, component: IntegrationComponent, operation: str, 
                        duration: float, success: bool = True, **metadata):
        """Record performance metrics for an operation."""
        key = f"{component.value}:{operation}"
        
        if key not in self.metrics:
            self.metrics[key] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_duration": 0.0,
                "min_duration": float('inf'),
                "max_duration": 0.0,
                "avg_duration": 0.0
            }
        
        metrics = self.metrics[key]
        metrics["total_calls"] += 1
        
        if success:
            metrics["successful_calls"] += 1
        else:
            metrics["failed_calls"] += 1
        
        metrics["total_duration"] += duration
        metrics["min_duration"] = min(metrics["min_duration"], duration)
        metrics["max_duration"] = max(metrics["max_duration"], duration)
        metrics["avg_duration"] = metrics["total_duration"] / metrics["total_calls"]
        
        # Log performance data
        self.logger.log_operation(
            "performance_metric",
            level="debug",
            component=component.value,
            operation=operation,
            duration=duration,
            success=success,
            **metadata
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a performance report for all monitored operations."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "operations": {}
        }
        
        for key, metrics in self.metrics.items():
            component, operation = key.split(":", 1)
            
            if component not in report["operations"]:
                report["operations"][component] = {}
            
            success_rate = (metrics["successful_calls"] / metrics["total_calls"]) * 100 if metrics["total_calls"] > 0 else 0
            
            report["operations"][component][operation] = {
                **metrics,
                "success_rate_percent": round(success_rate, 2)
            }
        
        return report


# Global instances
error_handler = IntegrationErrorHandler()
performance_monitor = PerformanceMonitor()


# Convenience functions for common logging patterns
def log_file_storage_operation(operation: str):
    """Decorator for file storage operations."""
    return log_integration_operation(IntegrationComponent.FILE_STORAGE, operation)


def log_github_operation(operation: str):
    """Decorator for GitHub operations."""
    return log_integration_operation(IntegrationComponent.GITHUB_API, operation)


def log_queue_operation(operation: str):
    """Decorator for queue operations."""
    return log_integration_operation(IntegrationComponent.JOB_QUEUE, operation)


def create_error_context(component: IntegrationComponent, operation: str, 
                        error: Exception, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                        user_id: Optional[int] = None, **metadata) -> ErrorContext:
    """Helper function to create error context from exception."""
    return ErrorContext(
        component=component,
        operation=operation,
        severity=severity,
        error_code=type(error).__name__,
        error_message=str(error),
        user_id=user_id,
        traceback_info=traceback.format_exc(),
        metadata=metadata
    )

class L
oggingConfig:
    """Configuration class for enhanced logging system."""
    
    def __init__(self):
        self.log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
        self.log_format = getattr(settings, 'LOG_FORMAT', 'structured')
        self.enable_file_logging = getattr(settings, 'ENABLE_FILE_LOGGING', True)
        self.enable_performance_monitoring = getattr(settings, 'ENABLE_PERFORMANCE_MONITORING', True)
        self.alert_thresholds = getattr(settings, 'ALERT_THRESHOLDS', {
            ErrorSeverity.LOW: 50,
            ErrorSeverity.MEDIUM: 20,
            ErrorSeverity.HIGH: 5,
            ErrorSeverity.CRITICAL: 1
        })
        self.log_retention_days = getattr(settings, 'LOG_RETENTION_DAYS', 30)
    
    def setup_logging(self):
        """Setup global logging configuration."""
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # Remove default handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        if self.log_format == 'structured':
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        root_logger.addHandler(console_handler)


class LogAnalyzer:
    """Analyze logs for patterns and insights."""
    
    def __init__(self):
        self.log_dir = Path("logs")
    
    def analyze_error_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze error patterns from the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        error_patterns = {}
        
        for log_file in self.log_dir.glob("*_errors.log"):
            component = log_file.stem.replace("_errors", "")
            error_patterns[component] = {
                "total_errors": 0,
                "error_types": {},
                "hourly_distribution": {}
            }
            
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            log_time = datetime.fromisoformat(log_entry.get('timestamp', ''))
                            
                            if log_time >= cutoff_time:
                                error_patterns[component]["total_errors"] += 1
                                
                                # Count error types
                                error_code = log_entry.get('error_code', 'Unknown')
                                if error_code not in error_patterns[component]["error_types"]:
                                    error_patterns[component]["error_types"][error_code] = 0
                                error_patterns[component]["error_types"][error_code] += 1
                                
                                # Hourly distribution
                                hour_key = log_time.strftime('%Y-%m-%d %H:00')
                                if hour_key not in error_patterns[component]["hourly_distribution"]:
                                    error_patterns[component]["hourly_distribution"][hour_key] = 0
                                error_patterns[component]["hourly_distribution"][hour_key] += 1
                                
                        except (json.JSONDecodeError, ValueError):
                            continue
                            
            except FileNotFoundError:
                continue
        
        return error_patterns
    
    def get_performance_insights(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance insights from logs."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        insights = {
            "slow_operations": [],
            "high_error_rate_operations": [],
            "performance_trends": {}
        }
        
        # Analyze performance from global performance monitor
        report = performance_monitor.get_performance_report()
        
        for component, operations in report.get("operations", {}).items():
            for operation, metrics in operations.items():
                # Identify slow operations (avg duration > 5 seconds)
                if metrics["avg_duration"] > 5.0:
                    insights["slow_operations"].append({
                        "component": component,
                        "operation": operation,
                        "avg_duration": metrics["avg_duration"],
                        "total_calls": metrics["total_calls"]
                    })
                
                # Identify high error rate operations (< 95% success rate)
                if metrics["success_rate_percent"] < 95.0:
                    insights["high_error_rate_operations"].append({
                        "component": component,
                        "operation": operation,
                        "success_rate": metrics["success_rate_percent"],
                        "failed_calls": metrics["failed_calls"],
                        "total_calls": metrics["total_calls"]
                    })
        
        return insights


class HealthCheckLogger:
    """Specialized logger for health check operations."""
    
    def __init__(self):
        self.logger = error_handler.get_logger(IntegrationComponent.HEALTH_CHECK)
    
    def log_health_check(self, service: str, status: str, response_time: float, 
                        details: Optional[Dict] = None):
        """Log a health check result."""
        self.logger.log_operation(
            "health_check",
            level="info" if status == "healthy" else "warning",
            service=service,
            status=status,
            response_time_ms=response_time * 1000,
            details=details or {}
        )
    
    def log_dependency_check(self, dependency: str, available: bool, 
                           error_message: Optional[str] = None):
        """Log a dependency availability check."""
        self.logger.log_operation(
            "dependency_check",
            level="info" if available else "error",
            dependency=dependency,
            available=available,
            error_message=error_message
        )


# Initialize logging configuration
logging_config = LoggingConfig()
health_check_logger = HealthCheckLogger()
log_analyzer = LogAnalyzer()


def setup_enhanced_logging():
    """Setup the enhanced logging system."""
    logging_config.setup_logging()
    
    # Log system startup
    logger = error_handler.get_logger(IntegrationComponent.CONFIGURATION)
    logger.log_operation(
        "system_startup",
        level="info",
        log_level=logging_config.log_level,
        log_format=logging_config.log_format,
        file_logging_enabled=logging_config.enable_file_logging,
        performance_monitoring_enabled=logging_config.enable_performance_monitoring
    )


def cleanup_old_logs():
    """Clean up old log files based on retention policy."""
    log_dir = Path("logs")
    if not log_dir.exists():
        return
    
    cutoff_date = datetime.utcnow() - timedelta(days=logging_config.log_retention_days)
    
    for log_file in log_dir.glob("*.log*"):
        try:
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                log_file.unlink()
                
                logger = error_handler.get_logger(IntegrationComponent.CONFIGURATION)
                logger.log_operation(
                    "log_cleanup",
                    level="info",
                    deleted_file=str(log_file),
                    file_age_days=(datetime.utcnow() - file_mtime).days
                )
        except Exception as e:
            # Log cleanup errors but don't fail
            logger = error_handler.get_logger(IntegrationComponent.CONFIGURATION)
            error_context = create_error_context(
                IntegrationComponent.CONFIGURATION,
                "log_cleanup",
                e,
                ErrorSeverity.LOW,
                metadata={"file": str(log_file)}
            )
            logger.log_error(error_context)


# Export commonly used functions and classes
__all__ = [
    'ErrorSeverity',
    'IntegrationComponent', 
    'ErrorContext',
    'IntegrationAlert',
    'EnhancedLogger',
    'IntegrationErrorHandler',
    'PerformanceMonitor',
    'LoggingConfig',
    'LogAnalyzer',
    'HealthCheckLogger',
    'log_integration_operation',
    'log_integration_context',
    'log_file_storage_operation',
    'log_github_operation',
    'log_queue_operation',
    'create_error_context',
    'error_handler',
    'performance_monitor',
    'health_check_logger',
    'log_analyzer',
    'setup_enhanced_logging',
    'cleanup_old_logs'
]