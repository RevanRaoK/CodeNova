"""
Redis caching service for analytics and file metadata.

This service provides:
- Redis connection management
- Cache operations (get, set, delete, invalidate)
- Cache warming strategies
- Performance monitoring
- Cache invalidation patterns

Requirements covered: 5.2, 5.4
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
import redis.asyncio as redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from app.core.queue_config import cache_config, monitoring_config

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service with advanced features."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self._connection_pool = None
        self._is_connected = False
        self._metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'total_response_time': 0.0,
            'operations_count': 0,
        }
    
    async def initialize(self) -> bool:
        """Initialize Redis connection and test connectivity."""
        try:
            if not self.redis_client:
                redis_config = cache_config.get_redis_config()
                self.redis_client = redis.from_url(
                    redis_config['url'],
                    decode_responses=False  # Keep as bytes for JSON handling
                )
            
            # Test connection
            await self.redis_client.ping()
            self._is_connected = True
            logger.info("Cache service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize cache service: {e}")
            self._is_connected = False
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self._is_connected = False
            logger.info("Cache service connection closed")
    
    async def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """
        Get value from cache with performance tracking.
        
        Args:
            key: Cache key
            cache_type: Type of cache for key prefixing
            
        Returns:
            Cached value or None if not found
        """
        if not self._is_connected:
            return None
        
        start_time = time.time()
        full_key = cache_config.get_cache_key(cache_type, key)
        
        try:
            value = await self.redis_client.get(full_key)
            
            if value is not None:
                self._metrics['hits'] += 1
                try:
                    # Try to deserialize JSON
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # Return as string if not JSON
                    return value
            else:
                self._metrics['misses'] += 1
                return None
                
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache get error for key {full_key}: {e}")
            self._metrics['errors'] += 1
            return None
        
        finally:
            response_time = time.time() - start_time
            self._metrics['total_response_time'] += response_time
            self._metrics['operations_count'] += 1
            
            # Log slow operations
            if response_time > (cache_config.CACHE_RESPONSE_TIME_THRESHOLD / 1000):
                logger.warning(f"Slow cache get operation: {response_time:.3f}s for key {full_key}")
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        cache_type: str = "default", 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cache for key prefixing and TTL
            ttl: Time to live in seconds (overrides default)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._is_connected:
            return False
        
        start_time = time.time()
        full_key = cache_config.get_cache_key(cache_type, key)
        
        if ttl is None:
            ttl = cache_config.get_cache_ttl(cache_type)
        
        try:
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            result = await self.redis_client.setex(full_key, ttl, value)
            
            if result:
                self._metrics['sets'] += 1
                return True
            else:
                return False
                
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache set error for key {full_key}: {e}")
            self._metrics['errors'] += 1
            return False
        
        finally:
            response_time = time.time() - start_time
            self._metrics['total_response_time'] += response_time
            self._metrics['operations_count'] += 1
            
            if response_time > (cache_config.CACHE_RESPONSE_TIME_THRESHOLD / 1000):
                logger.warning(f"Slow cache set operation: {response_time:.3f}s for key {full_key}")
    
    async def delete(self, key: str, cache_type: str = "default") -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            cache_type: Type of cache for key prefixing
            
        Returns:
            True if successful, False otherwise
        """
        if not self._is_connected:
            return False
        
        full_key = cache_config.get_cache_key(cache_type, key)
        
        try:
            result = await self.redis_client.delete(full_key)
            self._metrics['deletes'] += 1
            return result > 0
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache delete error for key {full_key}: {e}")
            self._metrics['errors'] += 1
            return False
    
    async def invalidate_pattern(self, pattern: str, cache_type: str = "default") -> int:
        """
        Invalidate cache keys matching a pattern.
        
        Args:
            pattern: Pattern to match (supports wildcards)
            cache_type: Type of cache for key prefixing
            
        Returns:
            Number of keys deleted
        """
        if not self._is_connected:
            return 0
        
        full_pattern = cache_config.get_cache_key(cache_type, pattern)
        
        try:
            keys = await self.redis_client.keys(full_pattern)
            
            if keys:
                deleted_count = await self.redis_client.delete(*keys)
                self._metrics['deletes'] += deleted_count
                logger.info(f"Invalidated {deleted_count} cache keys matching pattern: {full_pattern}")
                return deleted_count
            
            return 0
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache pattern invalidation error for pattern {full_pattern}: {e}")
            self._metrics['errors'] += 1
            return 0
    
    async def exists(self, key: str, cache_type: str = "default") -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            cache_type: Type of cache for key prefixing
            
        Returns:
            True if key exists, False otherwise
        """
        if not self._is_connected:
            return False
        
        full_key = cache_config.get_cache_key(cache_type, key)
        
        try:
            result = await self.redis_client.exists(full_key)
            return result > 0
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache exists check error for key {full_key}: {e}")
            self._metrics['errors'] += 1
            return False
    
    async def get_ttl(self, key: str, cache_type: str = "default") -> int:
        """
        Get TTL for a cache key.
        
        Args:
            key: Cache key
            cache_type: Type of cache for key prefixing
            
        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        if not self._is_connected:
            return -2
        
        full_key = cache_config.get_cache_key(cache_type, key)
        
        try:
            return await self.redis_client.ttl(full_key)
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache TTL check error for key {full_key}: {e}")
            self._metrics['errors'] += 1
            return -2
    
    async def extend_ttl(self, key: str, ttl: int, cache_type: str = "default") -> bool:
        """
        Extend TTL for an existing cache key.
        
        Args:
            key: Cache key
            ttl: New TTL in seconds
            cache_type: Type of cache for key prefixing
            
        Returns:
            True if successful, False otherwise
        """
        if not self._is_connected:
            return False
        
        full_key = cache_config.get_cache_key(cache_type, key)
        
        try:
            result = await self.redis_client.expire(full_key, ttl)
            return result
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache TTL extension error for key {full_key}: {e}")
            self._metrics['errors'] += 1
            return False
    
    async def get_or_set(
        self, 
        key: str, 
        fetch_func: Callable, 
        cache_type: str = "default", 
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or fetch and set if not found.
        
        Args:
            key: Cache key
            fetch_func: Async function to fetch data if not in cache
            cache_type: Type of cache for key prefixing
            ttl: Time to live in seconds
            
        Returns:
            Cached or fetched value
        """
        # Try to get from cache first
        cached_value = await self.get(key, cache_type)
        
        if cached_value is not None:
            return cached_value
        
        # Fetch data and cache it
        try:
            if asyncio.iscoroutinefunction(fetch_func):
                fetched_value = await fetch_func()
            else:
                fetched_value = fetch_func()
            
            if fetched_value is not None:
                await self.set(key, fetched_value, cache_type, ttl)
            
            return fetched_value
            
        except Exception as e:
            logger.error(f"Error in get_or_set for key {key}: {e}")
            return None
    
    async def warm_cache(self, warm_data: List[Dict[str, Any]]) -> int:
        """
        Warm cache with predefined data.
        
        Args:
            warm_data: List of dicts with 'key', 'value', 'cache_type', 'ttl'
            
        Returns:
            Number of successfully cached items
        """
        if not self._is_connected or not cache_config.CACHE_WARMING_ENABLED:
            return 0
        
        success_count = 0
        
        for item in warm_data:
            try:
                key = item['key']
                value = item['value']
                cache_type = item.get('cache_type', 'default')
                ttl = item.get('ttl')
                
                if await self.set(key, value, cache_type, ttl):
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Error warming cache item {item.get('key', 'unknown')}: {e}")
        
        logger.info(f"Cache warming completed: {success_count}/{len(warm_data)} items cached")
        return success_count
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache information and statistics.
        
        Returns:
            Dictionary with cache statistics and info
        """
        if not self._is_connected:
            return {'status': 'disconnected'}
        
        try:
            info = await self.redis_client.info()
            
            # Calculate hit rate
            total_operations = self._metrics['hits'] + self._metrics['misses']
            hit_rate = (self._metrics['hits'] / total_operations) if total_operations > 0 else 0
            
            # Calculate average response time
            avg_response_time = (
                self._metrics['total_response_time'] / self._metrics['operations_count']
                if self._metrics['operations_count'] > 0 else 0
            )
            
            return {
                'status': 'connected',
                'redis_info': {
                    'version': info.get('redis_version'),
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed'),
                },
                'cache_metrics': {
                    'hit_rate': round(hit_rate, 3),
                    'hits': self._metrics['hits'],
                    'misses': self._metrics['misses'],
                    'sets': self._metrics['sets'],
                    'deletes': self._metrics['deletes'],
                    'errors': self._metrics['errors'],
                    'avg_response_time_ms': round(avg_response_time * 1000, 2),
                    'total_operations': self._metrics['operations_count'],
                },
                'configuration': {
                    'default_ttl': cache_config.DEFAULT_CACHE_TTL,
                    'cache_warming_enabled': cache_config.CACHE_WARMING_ENABLED,
                    'invalidation_enabled': cache_config.CACHE_INVALIDATION_ENABLED,
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check.
        
        Returns:
            Health check results
        """
        health_status = {
            'healthy': False,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        try:
            # Test basic connectivity
            start_time = time.time()
            await self.redis_client.ping()
            ping_time = time.time() - start_time
            
            health_status['checks']['connectivity'] = {
                'status': 'pass',
                'response_time_ms': round(ping_time * 1000, 2)
            }
            
            # Test read/write operations
            test_key = f"health_check_{int(time.time())}"
            test_value = "health_check_value"
            
            await self.set(test_key, test_value, "default", 60)
            retrieved_value = await self.get(test_key, "default")
            await self.delete(test_key, "default")
            
            health_status['checks']['read_write'] = {
                'status': 'pass' if retrieved_value == test_value else 'fail',
                'test_successful': retrieved_value == test_value
            }
            
            # Check performance metrics
            cache_info = await self.get_cache_info()
            hit_rate = cache_info.get('cache_metrics', {}).get('hit_rate', 0)
            avg_response_time = cache_info.get('cache_metrics', {}).get('avg_response_time_ms', 0)
            
            health_status['checks']['performance'] = {
                'status': 'pass' if (
                    hit_rate >= cache_config.CACHE_HIT_RATE_THRESHOLD and 
                    avg_response_time <= cache_config.CACHE_RESPONSE_TIME_THRESHOLD
                ) else 'warn',
                'hit_rate': hit_rate,
                'avg_response_time_ms': avg_response_time,
                'hit_rate_threshold': cache_config.CACHE_HIT_RATE_THRESHOLD,
                'response_time_threshold': cache_config.CACHE_RESPONSE_TIME_THRESHOLD
            }
            
            # Overall health status
            all_checks_pass = all(
                check['status'] in ['pass', 'warn'] 
                for check in health_status['checks'].values()
            )
            
            health_status['healthy'] = all_checks_pass
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            health_status['checks']['connectivity'] = {
                'status': 'fail',
                'error': str(e)
            }
        
        return health_status
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self._metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'total_response_time': 0.0,
            'operations_count': 0,
        }
        logger.info("Cache metrics reset")
    
    # Synchronous methods for Celery tasks
    def get_sync(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """Synchronous version of get method for Celery tasks."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.get(key, cache_type))
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.get(key, cache_type))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Sync cache get error: {e}")
            return None
    
    def set_sync(self, key: str, value: Any, cache_type: str = "default", ttl: Optional[int] = None) -> bool:
        """Synchronous version of set method for Celery tasks."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.set(key, value, cache_type, ttl))
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.set(key, value, cache_type, ttl))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Sync cache set error: {e}")
            return False


# Global cache service instance
cache_service = CacheService()


# Utility functions for common cache operations
async def get_cached_analytics(key: str) -> Optional[Any]:
    """Get analytics data from cache."""
    return await cache_service.get(key, "analytics")


async def set_cached_analytics(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set analytics data in cache."""
    return await cache_service.set(key, value, "analytics", ttl)


async def get_cached_file_metadata(file_id: str) -> Optional[Any]:
    """Get file metadata from cache."""
    return await cache_service.get(f"metadata:{file_id}", "file")


async def set_cached_file_metadata(file_id: str, metadata: Dict[str, Any], ttl: Optional[int] = None) -> bool:
    """Set file metadata in cache."""
    return await cache_service.set(f"metadata:{file_id}", metadata, "file", ttl)


async def invalidate_user_cache(user_id: int):
    """Invalidate all cache entries for a specific user."""
    patterns = [
        f"user:{user_id}:*",
        f"analytics:user:{user_id}:*",
        f"file:user:{user_id}:*"
    ]
    
    total_deleted = 0
    for pattern in patterns:
        deleted = await cache_service.invalidate_pattern(pattern)
        total_deleted += deleted
    
    logger.info(f"Invalidated {total_deleted} cache entries for user {user_id}")
    return total_deleted


async def initialize_cache_service() -> bool:
    """Initialize the global cache service."""
    return await cache_service.initialize()


async def close_cache_service():
    """Close the global cache service."""
    await cache_service.close()