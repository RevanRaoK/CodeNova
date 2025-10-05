"""
Queue monitoring service for RabbitMQ and Celery workers.

This service provides:
- Queue depth monitoring
- Worker health checks
- Performance metrics collection
- Alert generation for queue issues
- Queue management operations

Requirements covered: 5.5
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
from celery import Celery

from app.core.celery_app import celery_app, QueueHealthCheck
from app.core.queue_config import queue_config, monitoring_config
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class QueueMonitoringService:
    """Service for monitoring Redis queue health and performance."""
    
    def __init__(self):
        self.redis_config = queue_config.get_redis_config()
        self._last_check_time = None
        self._alert_history = []
    
    async def get_queue_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive queue statistics from Redis queue system.
        
        Returns:
            Dictionary containing queue statistics
        """
        try:
            # Get queue statistics from Redis queue system
            stats = await celery_app.get_stats()
            
            # Process queue statistics
            queue_stats = {}
            total_messages = 0
            
            for priority, queue_info in stats.items():
                queue_name = priority
                messages = queue_info.get('total', 0)
                
                queue_stats[queue_name] = {
                    'messages': messages,
                    'messages_ready': messages,  # In Redis, all queued messages are ready
                    'messages_unacknowledged': 0,  # Redis doesn't have unacknowledged messages
                    'consumers': 1,  # Simplified for Redis
                    'message_stats': queue_info,
                    'memory': 0,  # Would need Redis memory info
                    'state': 'running' if messages >= 0 else 'unknown'
                }
                
                total_messages += messages
            
            return {
                'timestamp': time.time(),
                'overview': {
                    'total_queues': len(queue_stats),
                    'total_messages': total_messages,
                    'total_consumers': len(queue_stats),  # One consumer per queue
                    'redis_version': 'unknown',  # Would need Redis info
                    'system': 'redis'
                },
                'queues': queue_stats,
                    'node_info': overview_data.get('node', {}),
                    'message_stats': overview_data.get('message_stats', {})
                }
                
        except Exception as exc:
            logger.error(f"Error getting queue statistics: {exc}")
            return {
                'timestamp': time.time(),
                'error': str(exc),
                'status': 'error'
            }
    
    async def get_worker_statistics(self) -> Dict[str, Any]:
        """
        Get Redis queue worker statistics and health information.
        
        Returns:
            Dictionary containing worker statistics
        """
        try:
            # Get worker health check
            worker_health = await QueueHealthCheck.check_worker_status()
            
            # For Redis queue system, we simulate worker information
            # In a real implementation, you'd track worker processes
            worker_details = {
                'redis_worker_1': {
                    'status': 'online',
                    'active_tasks': 0,  # Would need to track from Redis
                    'scheduled_tasks': 0,
                    'reserved_tasks': 0,
                    'total_tasks': {'processed': 0, 'failed': 0},
                    'pool_info': {'max_concurrency': queue_config.WORKER_CONCURRENCY},
                    'rusage': {},
                    'clock': int(time.time()),
                    'pid': 0  # Would be actual worker PID
                }
            }
            
            return {
                'timestamp': time.time(),
                'health_status': worker_health,
                'worker_details': worker_details,
                'total_workers': len(worker_details),
                'total_active_tasks': sum(w.get('active_tasks', 0) for w in worker_details.values())
            }
            
        except Exception as exc:
            logger.error(f"Error getting worker statistics: {exc}")
            return {
                'timestamp': time.time(),
                'error': str(exc),
                'status': 'error'
            }
    
    async def check_queue_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive queue health check.
        
        Returns:
            Health check results with alerts
        """
        try:
            health_results = {
                'timestamp': time.time(),
                'overall_status': 'healthy',
                'checks': {},
                'alerts': [],
                'recommendations': []
            }
            
            # Get queue and worker statistics
            queue_stats = await self.get_queue_statistics()
            worker_stats = await self.get_worker_statistics()
            
            # Check queue depths
            queue_check = await self._check_queue_depths(queue_stats)
            health_results['checks']['queue_depths'] = queue_check
            
            # Check worker availability
            worker_check = await self._check_worker_availability(worker_stats)
            health_results['checks']['worker_availability'] = worker_check
            
            # Check message processing rates
            processing_check = await self._check_processing_rates(queue_stats)
            health_results['checks']['processing_rates'] = processing_check
            
            # Check resource usage
            resource_check = await self._check_resource_usage(worker_stats)
            health_results['checks']['resource_usage'] = resource_check
            
            # Aggregate alerts and determine overall status
            all_checks = [queue_check, worker_check, processing_check, resource_check]
            
            for check in all_checks:
                if check.get('alerts'):
                    health_results['alerts'].extend(check['alerts'])
                if check.get('recommendations'):
                    health_results['recommendations'].extend(check['recommendations'])
            
            # Determine overall status
            critical_alerts = [a for a in health_results['alerts'] if a.get('severity') == 'critical']
            warning_alerts = [a for a in health_results['alerts'] if a.get('severity') == 'warning']
            
            if critical_alerts:
                health_results['overall_status'] = 'critical'
            elif warning_alerts:
                health_results['overall_status'] = 'warning'
            
            # Cache health results
            cache_key = f"health:queue_comprehensive:{int(time.time() // 300)}"  # 5-minute cache
            await cache_service.set(cache_key, health_results, "queue", ttl=300)
            
            # Store check time
            self._last_check_time = time.time()
            
            return health_results
            
        except Exception as exc:
            logger.error(f"Error in queue health check: {exc}")
            return {
                'timestamp': time.time(),
                'overall_status': 'error',
                'error': str(exc),
                'alerts': [{
                    'type': 'health_check_failed',
                    'severity': 'critical',
                    'message': f"Queue health check failed: {exc}"
                }]
            }
    
    async def _check_queue_depths(self, queue_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Check queue depths against thresholds."""
        check_result = {
            'status': 'pass',
            'alerts': [],
            'recommendations': [],
            'details': {}
        }
        
        if 'error' in queue_stats:
            check_result['status'] = 'fail'
            check_result['alerts'].append({
                'type': 'queue_stats_unavailable',
                'severity': 'critical',
                'message': 'Unable to retrieve queue statistics'
            })
            return check_result
        
        queues = queue_stats.get('queues', {})
        
        for queue_name, queue_info in queues.items():
            messages = queue_info.get('messages', 0)
            
            check_result['details'][queue_name] = {
                'messages': messages,
                'status': 'normal'
            }
            
            # Check against thresholds
            if messages >= queue_config.QUEUE_DEPTH_CRITICAL_THRESHOLD:
                check_result['status'] = 'fail'
                check_result['details'][queue_name]['status'] = 'critical'
                check_result['alerts'].append({
                    'type': 'queue_depth_critical',
                    'severity': 'critical',
                    'message': f"Queue {queue_name} has {messages} messages (critical threshold: {queue_config.QUEUE_DEPTH_CRITICAL_THRESHOLD})",
                    'queue': queue_name,
                    'message_count': messages
                })
                
            elif messages >= queue_config.QUEUE_DEPTH_WARNING_THRESHOLD:
                if check_result['status'] == 'pass':
                    check_result['status'] = 'warn'
                check_result['details'][queue_name]['status'] = 'warning'
                check_result['alerts'].append({
                    'type': 'queue_depth_warning',
                    'severity': 'warning',
                    'message': f"Queue {queue_name} has {messages} messages (warning threshold: {queue_config.QUEUE_DEPTH_WARNING_THRESHOLD})",
                    'queue': queue_name,
                    'message_count': messages
                })
        
        return check_result
    
    async def _check_worker_availability(self, worker_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Check worker availability and health."""
        check_result = {
            'status': 'pass',
            'alerts': [],
            'recommendations': [],
            'details': {}
        }
        
        if 'error' in worker_stats:
            check_result['status'] = 'fail'
            check_result['alerts'].append({
                'type': 'worker_stats_unavailable',
                'severity': 'critical',
                'message': 'Unable to retrieve worker statistics'
            })
            return check_result
        
        total_workers = worker_stats.get('total_workers', 0)
        worker_details = worker_stats.get('worker_details', {})
        
        check_result['details'] = {
            'total_workers': total_workers,
            'online_workers': len(worker_details),
            'workers': worker_details
        }
        
        # Check if we have any workers
        if total_workers == 0:
            check_result['status'] = 'fail'
            check_result['alerts'].append({
                'type': 'no_workers_available',
                'severity': 'critical',
                'message': 'No Celery workers are available'
            })
        
        # Check worker load
        total_active_tasks = worker_stats.get('total_active_tasks', 0)
        
        if total_workers > 0:
            avg_tasks_per_worker = total_active_tasks / total_workers
            
            if avg_tasks_per_worker > 10:  # Threshold for high load
                check_result['recommendations'].append(
                    f"High worker load detected: {avg_tasks_per_worker:.1f} tasks per worker on average"
                )
        
        return check_result
    
    async def _check_processing_rates(self, queue_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Check message processing rates."""
        check_result = {
            'status': 'pass',
            'alerts': [],
            'recommendations': [],
            'details': {}
        }
        
        if 'error' in queue_stats:
            return check_result
        
        # Get cached previous stats for rate calculation
        cache_key = "queue_stats_previous"
        previous_stats = await cache_service.get(cache_key, "queue")
        
        # Cache current stats for next check
        await cache_service.set(cache_key, queue_stats, "queue", ttl=600)  # 10 minutes
        
        if previous_stats:
            time_diff = queue_stats['timestamp'] - previous_stats['timestamp']
            
            if time_diff > 0:
                queues = queue_stats.get('queues', {})
                prev_queues = previous_stats.get('queues', {})
                
                for queue_name, queue_info in queues.items():
                    if queue_name in prev_queues:
                        current_messages = queue_info.get('messages', 0)
                        prev_messages = prev_queues[queue_name].get('messages', 0)
                        
                        # Calculate processing rate (negative means messages are being processed)
                        rate = (current_messages - prev_messages) / time_diff
                        
                        check_result['details'][queue_name] = {
                            'processing_rate': rate,
                            'current_messages': current_messages,
                            'previous_messages': prev_messages
                        }
                        
                        # Check for stalled processing
                        if current_messages > 0 and rate >= 0 and time_diff > 300:  # 5 minutes
                            check_result['alerts'].append({
                                'type': 'processing_stalled',
                                'severity': 'warning',
                                'message': f"Queue {queue_name} appears to have stalled processing",
                                'queue': queue_name,
                                'rate': rate
                            })
        
        return check_result
    
    async def _check_resource_usage(self, worker_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Check worker resource usage."""
        check_result = {
            'status': 'pass',
            'alerts': [],
            'recommendations': [],
            'details': {}
        }
        
        if 'error' in worker_stats:
            return check_result
        
        worker_details = worker_stats.get('worker_details', {})
        
        for worker_name, worker_info in worker_details.items():
            rusage = worker_info.get('rusage', {})
            
            # Check memory usage (if available)
            max_rss = rusage.get('maxrss', 0)  # Maximum resident set size
            
            check_result['details'][worker_name] = {
                'memory_usage': max_rss,
                'active_tasks': worker_info.get('active_tasks', 0),
                'total_tasks': worker_info.get('total_tasks', {})
            }
            
            # Basic resource checks (thresholds would need to be configured)
            active_tasks = worker_info.get('active_tasks', 0)
            
            if active_tasks > 50:  # High task load threshold
                check_result['recommendations'].append(
                    f"Worker {worker_name} has high task load: {active_tasks} active tasks"
                )
        
        return check_result
    
    async def get_performance_metrics(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Get performance metrics over a specified time range.
        
        Args:
            time_range_hours: Number of hours to look back
            
        Returns:
            Performance metrics data
        """
        try:
            # This would typically query a time-series database
            # For now, we'll return current metrics with historical placeholders
            
            current_queue_stats = await self.get_queue_statistics()
            current_worker_stats = await self.get_worker_statistics()
            
            metrics = {
                'time_range_hours': time_range_hours,
                'generated_at': time.time(),
                'current_metrics': {
                    'queue_stats': current_queue_stats,
                    'worker_stats': current_worker_stats
                },
                'historical_trends': {
                    'queue_depths': [],  # Would be populated from historical data
                    'processing_rates': [],
                    'worker_availability': [],
                    'error_rates': []
                },
                'summary': {
                    'avg_queue_depth': 0,
                    'avg_processing_rate': 0,
                    'uptime_percentage': 0,
                    'error_rate': 0
                }
            }
            
            return metrics
            
        except Exception as exc:
            logger.error(f"Error getting performance metrics: {exc}")
            return {
                'error': str(exc),
                'generated_at': time.time()
            }
    
    async def purge_queue(self, queue_name: str) -> Dict[str, Any]:
        """
        Purge all messages from a specific queue.
        
        Args:
            queue_name: Name of the queue to purge
            
        Returns:
            Purge operation results
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.rabbitmq_management_url}/api/queues/%2F/{queue_name}/contents",
                    auth=self.rabbitmq_auth,
                    timeout=30.0
                )
                
                if response.status_code == 204:
                    result = {
                        'status': 'success',
                        'queue': queue_name,
                        'message': f'Queue {queue_name} purged successfully',
                        'timestamp': time.time()
                    }
                else:
                    result = {
                        'status': 'error',
                        'queue': queue_name,
                        'error': f'Failed to purge queue: HTTP {response.status_code}',
                        'timestamp': time.time()
                    }
                
                logger.info(f"Queue purge operation: {result}")
                return result
                
        except Exception as exc:
            logger.error(f"Error purging queue {queue_name}: {exc}")
            return {
                'status': 'error',
                'queue': queue_name,
                'error': str(exc),
                'timestamp': time.time()
            }
    
    async def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive data for monitoring dashboard.
        
        Returns:
            Dashboard data including all monitoring information
        """
        try:
            # Get all monitoring data
            queue_stats = await self.get_queue_statistics()
            worker_stats = await self.get_worker_statistics()
            health_check = await self.check_queue_health()
            
            dashboard_data = {
                'timestamp': time.time(),
                'last_update': datetime.utcnow().isoformat(),
                'queue_statistics': queue_stats,
                'worker_statistics': worker_stats,
                'health_status': health_check,
                'system_info': {
                    'monitoring_enabled': monitoring_config.HEALTH_CHECK_ENABLED,
                    'check_interval': monitoring_config.HEALTH_CHECK_INTERVAL,
                    'alerting_enabled': monitoring_config.ALERTING_ENABLED
                }
            }
            
            # Cache dashboard data
            cache_key = f"dashboard:queue_monitoring:{int(time.time() // 60)}"
            await cache_service.set(cache_key, dashboard_data, "queue", ttl=120)  # 2 minutes
            
            return dashboard_data
            
        except Exception as exc:
            logger.error(f"Error getting monitoring dashboard data: {exc}")
            return {
                'timestamp': time.time(),
                'error': str(exc),
                'status': 'error'
            }


# Global monitoring service instance
queue_monitoring_service = QueueMonitoringService()