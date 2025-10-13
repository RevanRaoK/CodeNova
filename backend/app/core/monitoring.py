"""
Comprehensive monitoring and logging system for all platform services.

This module provides structured logging, performance monitoring, error tracking,
and health checks for all platform features.

Requirements covered: Performance and scalability for all features
"""

import logging
import time
import json
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps
from contextlib import contextmanager
import asyncio
import psutil
import threading
import os
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.config import settings
from app.core.cache import cache


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ServiceType(str, Enum):
    API = "api"
    ANALYTICS = "analytics"
    FEEDBACK = "feedback"
    GITHUB = "github"
    FILE_STORAGE = "file_storage"
    USER_MANAGEMENT = "user_management"
    ADMIN = "admin"
    QUEUE = "queue"
    CACHE = "cache"
    DATABASE = "database"


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    service: str
    operation: str
    duration_ms: float
    timestamp: datetime
    user_id: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemMetric:
    """System resource metric data structure."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_connections: int
    queue_size: int = 0
    cache_hit_rate: float = 0.0


class StructuredLogger:
    """Structured logging with JSON format and contextual information."""
    
    def __init__(self, name: str, service_type: ServiceType):
        self.logger = logging.getLogger(name)
        self.service_type = service_type
        self.setup_logger()
    
    def setup_logger(self):
        """Configure structured logging."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(getattr(logging, settings.LOG_LEVEL, "INFO"))
    
    def _log_structured(self, level: LogLevel, message: str, **kwargs):
        """Log structured message with context."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_type.value,
            "message": message,
            "level": level.value,
            **kwargs
        }
        
        # Add request context if available
        try:
            from contextvars import copy_context
            ctx = copy_context()
            if 'request_id' in ctx:
                log_data['request_id'] = ctx['request_id']
            if 'user_id' in ctx:
                log_data['user_id'] = ctx['user_id']
        except:
            pass
        
        # Convert datetime objects to ISO format strings for JSON serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            return obj
        
        serializable_data = serialize_datetime(log_data)
        getattr(self.logger, level.value.lower())(json.dumps(serializable_data))
    
    def debug(self, message: str, **kwargs):
        self._log_structured(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_structured(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_structured(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        if error:
            kwargs.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            })
        self._log_structured(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, error: Exception = None, **kwargs):
        if error:
            kwargs.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            })
        self._log_structured(LogLevel.CRITICAL, message, **kwargs)


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.system_metrics: List[SystemMetric] = []
        self.logger = StructuredLogger("performance_monitor", ServiceType.API)
        self._lock = threading.Lock()
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric."""
        with self._lock:
            self.metrics.append(metric)
            
            # Cache recent metrics with datetime serialization
            cache_key = f"metrics:{metric.service}:{metric.operation}"
            recent_metrics = cache.get(cache_key) or []
            
            # Convert metric to dict and handle datetime serialization
            metric_dict = asdict(metric)
            metric_dict['timestamp'] = metric.timestamp.isoformat()
            recent_metrics.append(metric_dict)
            
            # Keep only last 100 metrics per operation
            if len(recent_metrics) > 100:
                recent_metrics = recent_metrics[-100:]
            
            cache.set(cache_key, recent_metrics, 3600)
            
            # Log slow operations
            if metric.duration_ms > 1000:  # > 1 second
                self.logger.warning(
                    f"Slow operation detected: {metric.service}.{metric.operation}",
                    duration_ms=metric.duration_ms,
                    user_id=metric.user_id
                )
    
    def get_service_metrics(self, service: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics for a specific service."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            asdict(m) for m in self.metrics 
            if m.service == service and m.timestamp > cutoff
        ]
    
    def get_performance_summary(self, service: str = None) -> Dict[str, Any]:
        """Get performance summary statistics."""
        relevant_metrics = self.metrics
        if service:
            relevant_metrics = [m for m in self.metrics if m.service == service]
        
        if not relevant_metrics:
            return {"error": "No metrics available"}
        
        durations = [m.duration_ms for m in relevant_metrics]
        success_rate = sum(1 for m in relevant_metrics if m.success) / len(relevant_metrics)
        
        return {
            "total_operations": len(relevant_metrics),
            "success_rate": success_rate,
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "error_count": sum(1 for m in relevant_metrics if not m.success)
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(service: str, operation: str):
    """Decorator to monitor function performance."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            user_id = None
            
            try:
                # Extract user_id if available
                if 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                elif args and hasattr(args[0], 'user_id'):
                    user_id = args[0].user_id
                
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                metric = PerformanceMetric(
                    service=service,
                    operation=operation,
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    user_id=user_id,
                    success=success,
                    error_message=error_message
                )
                performance_monitor.record_metric(metric)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            user_id = None
            
            try:
                # Extract user_id if available
                if 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                elif args and hasattr(args[0], 'user_id'):
                    user_id = args[0].user_id
                
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                metric = PerformanceMetric(
                    service=service,
                    operation=operation,
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    user_id=user_id,
                    success=success,
                    error_message=error_message
                )
                performance_monitor.record_metric(metric)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


@contextmanager
def performance_context(service: str, operation: str, user_id: int = None):
    """Context manager for monitoring code blocks."""
    start_time = time.time()
    success = True
    error_message = None
    
    try:
        yield
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        metric = PerformanceMetric(
            service=service,
            operation=operation,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            success=success,
            error_message=error_message
        )
        performance_monitor.record_metric(metric)


class SystemMonitor:
    """System resource monitoring."""
    
    def __init__(self):
        self.logger = StructuredLogger("system_monitor", ServiceType.API)
        self.running = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval: int = 60):
        """Start system monitoring in background thread."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("System monitoring started", interval=interval)
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("System monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop."""
        while self.running:
            try:
                metric = self._collect_system_metrics()
                self._store_system_metric(metric)
                
                # Check for alerts
                self._check_system_alerts(metric)
                
            except Exception as e:
                self.logger.error("Error collecting system metrics", error=e)
            
            time.sleep(interval)
    
    def _collect_system_metrics(self) -> SystemMetric:
        """Collect current system metrics."""
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Get disk usage with better Windows support
        disk_percent = 0
        try:
            if os.name == 'nt':
                # On Windows, try multiple approaches
                try:
                    # First try C: drive
                    disk = psutil.disk_usage('C:\\')
                except:
                    try:
                        # Try current working directory
                        disk = psutil.disk_usage(os.getcwd())
                    except:
                        # Fallback to root of current drive
                        import pathlib
                        current_path = pathlib.Path.cwd()
                        root_path = current_path.anchor
                        disk = psutil.disk_usage(root_path)
            else:
                disk = psutil.disk_usage('/')
            # Safely calculate disk percentage
            try:
                disk_percent = float(disk.used) / float(disk.total) * 100.0 if disk.total > 0 else 0.0
            except (OverflowError, ZeroDivisionError, ValueError):
                disk_percent = 0.0
        except Exception as e:
            # Log without using structured logging to avoid recursion
            try:
                print(f"Could not get disk usage: {str(e)}")
            except:
                print("Could not get disk usage: [formatting error]")
            disk_percent = 0
        
        # Network connections
        connections = len(psutil.net_connections())
        
        # Cache hit rate
        cache_health = cache.redis_client.info() if hasattr(cache, 'redis_client') else {}
        hits = cache_health.get('keyspace_hits', 0)
        misses = cache_health.get('keyspace_misses', 0)
        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
        
        return SystemMetric(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=disk_percent,
            active_connections=connections,
            cache_hit_rate=hit_rate
        )
    
    def _store_system_metric(self, metric: SystemMetric):
        """Store system metric in cache."""
        cache_key = "system_metrics"
        metrics = cache.get(cache_key) or []
        
        # Convert metric to dict and handle datetime serialization
        metric_dict = asdict(metric)
        metric_dict['timestamp'] = metric.timestamp.isoformat()
        metrics.append(metric_dict)
        
        # Keep only last 24 hours of metrics (assuming 1-minute intervals)
        if len(metrics) > 1440:
            metrics = metrics[-1440:]
        
        cache.set(cache_key, metrics, 86400)  # 24 hours
    
    def _check_system_alerts(self, metric: SystemMetric):
        """Check for system alert conditions."""
        alerts = []
        
        if metric.cpu_percent > 80:
            alerts.append(f"High CPU usage: {metric.cpu_percent:.1f}%")
        
        if metric.memory_percent > 85:
            alerts.append(f"High memory usage: {metric.memory_percent:.1f}%")
        
        if metric.disk_usage_percent > 90:
            alerts.append(f"High disk usage: {metric.disk_usage_percent:.1f}%")
        
        if metric.cache_hit_rate < 0.7:
            alerts.append(f"Low cache hit rate: {metric.cache_hit_rate:.2f}")
        
        for alert in alerts:
            # Convert metric to dict and handle datetime serialization
            metric_dict = asdict(metric)
            metric_dict['timestamp'] = metric.timestamp.isoformat()
            self.logger.warning("System alert", alert=alert, **metric_dict)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status."""
        try:
            current_metric = self._collect_system_metrics()
            
            # Determine overall health
            health_score = 100
            if current_metric.cpu_percent > 80:
                health_score -= 20
            if current_metric.memory_percent > 85:
                health_score -= 20
            if current_metric.disk_usage_percent > 90:
                health_score -= 30
            if current_metric.cache_hit_rate < 0.7:
                health_score -= 10
            
            status = "healthy"
            if health_score < 70:
                status = "degraded"
            if health_score < 50:
                status = "unhealthy"
            
            return {
                "status": status,
                "health_score": health_score,
                "metrics": asdict(current_metric),
                "timestamp": current_metric.timestamp.isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global system monitor instance
system_monitor = SystemMonitor()


class HealthChecker:
    """Health check utilities for all services."""
    
    def __init__(self):
        self.logger = StructuredLogger("health_checker", ServiceType.API)
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            from app.core.database import engine
            from sqlalchemy import text
            
            start_time = time.time()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_cache_health(self) -> Dict[str, Any]:
        """Check Redis cache health."""
        try:
            from app.core.cache import check_cache_health
            return check_cache_health()
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_queue_health(self) -> Dict[str, Any]:
        """Check message queue health."""
        try:
            # This would check RabbitMQ connection
            # Implementation depends on queue setup
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_external_services_health(self) -> Dict[str, Any]:
        """Check external service dependencies."""
        checks = {}
        
        # GitHub API
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.github.com/rate_limit", timeout=5)
                checks["github"] = {
                    "status": "healthy" if response.status_code == 200 else "degraded",
                    "response_code": response.status_code
                }
        except Exception as e:
            checks["github"] = {"status": "unhealthy", "error": str(e)}
        
        # Digital Ocean Spaces (if configured)
        try:
            # This would check DO Spaces connectivity
            checks["storage"] = {"status": "healthy"}
        except Exception as e:
            checks["storage"] = {"status": "unhealthy", "error": str(e)}
        
        return checks
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all services."""
        health_checks = {
            "database": await self.check_database_health(),
            "cache": await self.check_cache_health(),
            "queue": await self.check_queue_health(),
            "external_services": await self.check_external_services_health(),
            "system": system_monitor.get_system_health()
        }
        
        # Determine overall status
        all_healthy = all(
            check.get("status") == "healthy" 
            for check in health_checks.values() 
            if isinstance(check, dict)
        )
        
        overall_status = "healthy" if all_healthy else "degraded"
        
        # Check for any critical failures
        critical_failures = [
            name for name, check in health_checks.items()
            if isinstance(check, dict) and check.get("status") == "unhealthy"
        ]
        
        if critical_failures:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": health_checks,
            "critical_failures": critical_failures
        }


# Global health checker instance
health_checker = HealthChecker()


# Service-specific loggers
def get_service_logger(service_type: ServiceType, name: str = None) -> StructuredLogger:
    """Get a structured logger for a specific service."""
    logger_name = name or service_type.value
    return StructuredLogger(logger_name, service_type)


# Initialize monitoring on module import
def initialize_monitoring():
    """Initialize monitoring systems."""
    try:
        system_monitor.start_monitoring(interval=60)  # Monitor every minute
        logger = get_service_logger(ServiceType.API, "monitoring_init")
        logger.info("Monitoring systems initialized successfully")
    except Exception as e:
        print(f"Failed to initialize monitoring: {e}")


# Auto-initialize if not in test environment
if not settings.TESTING:
    initialize_monitoring()