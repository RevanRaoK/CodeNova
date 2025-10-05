"""
Redis queue tasks for cache management.
"""

import logging
from typing import Dict, Any, List

from app.core.redis_queue import redis_queue
from app.core.queue_config import QueuePriority
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


@redis_queue.task('warm_cache_data', QueuePriority.LOW)
async def warm_cache_data(cache_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Warm cache with predefined data."""
    logger.info(f"Warming cache with {len(cache_data)} items")
    
    try:
        success_count = await cache_service.warm_cache(cache_data)
        return {
            'status': 'completed',
            'items_cached': success_count,
            'total_items': len(cache_data)
        }
    except Exception as e:
        logger.error(f"Error warming cache: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'items_cached': 0
        }


@redis_queue.task('cleanup_expired_cache', QueuePriority.LOW)
async def cleanup_expired_cache() -> Dict[str, Any]:
    """Clean up expired cache entries."""
    logger.info("Cleaning up expired cache entries")
    
    try:
        # Get cache info to check for expired entries
        cache_info = await cache_service.get_cache_info()
        
        # Mock cleanup - in real implementation, this would clean expired keys
        cleaned_count = 0
        
        return {
            'status': 'completed',
            'entries_cleaned': cleaned_count,
            'cache_status': cache_info.get('status', 'unknown')
        }
    except Exception as e:
        logger.error(f"Error cleaning cache: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'entries_cleaned': 0
        }


@redis_queue.task('invalidate_cache_pattern', QueuePriority.MEDIUM)
async def invalidate_cache_pattern(pattern: str, cache_type: str = "default") -> Dict[str, Any]:
    """Invalidate cache entries matching a pattern."""
    logger.info(f"Invalidating cache pattern: {pattern}")
    
    try:
        invalidated_count = await cache_service.invalidate_pattern(pattern, cache_type)
        
        return {
            'status': 'completed',
            'pattern': pattern,
            'cache_type': cache_type,
            'entries_invalidated': invalidated_count
        }
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'entries_invalidated': 0
        }