"""
Redis caching layer for frequently accessed data.

This module provides caching utilities for analytics, user data, and GitHub integration
to improve performance across all platform features.

Requirements covered: Performance and scalability for all features
"""

import json
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis
from functools import wraps
import hashlib
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager with automatic serialization and TTL management."""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=False,  # We handle encoding ourselves
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for Redis storage."""
        try:
            # Try JSON first for simple data types
            return json.dumps(data, default=str).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from Redis storage."""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        try:
            serialized = self._serialize(value)
            return self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1, ttl: int = 3600) -> Optional[int]:
        """Increment counter with TTL."""
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key, amount)
            pipe.expire(key, ttl)
            result = pipe.execute()
            return result[0]
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None


# Global cache instance
cache = CacheManager()


# Cache key generators
class CacheKeys:
    """Cache key generators for different data types."""
    
    @staticmethod
    def user_analytics(user_id: int, days: int = 30) -> str:
        return f"analytics:user:{user_id}:days:{days}"
    
    @staticmethod
    def team_analytics(team_id: str) -> str:
        return f"analytics:team:{team_id}"
    
    @staticmethod
    def feedback_summary(user_id: int, period: str = "30d") -> str:
        return f"feedback:summary:{user_id}:{period}"
    
    @staticmethod
    def github_repo_stats(repo_id: str) -> str:
        return f"github:repo:{repo_id}:stats"
    
    @staticmethod
    def user_profile(user_id: int) -> str:
        return f"user:profile:{user_id}"
    
    @staticmethod
    def pr_analysis_results(pr_id: str) -> str:
        return f"pr:analysis:{pr_id}"
    
    @staticmethod
    def file_metadata(file_id: str) -> str:
        return f"file:metadata:{file_id}"
    
    @staticmethod
    def rate_limit(user_id: int, endpoint: str) -> str:
        return f"rate_limit:{user_id}:{endpoint}"
    
    @staticmethod
    def session_data(session_id: str) -> str:
        return f"session:{session_id}"


def cache_result(ttl: int = 3600, key_func: callable = None):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result
        
        return wrapper
    return decorator


class AnalyticsCache:
    """Specialized caching for analytics data."""
    
    @staticmethod
    def get_user_feedback_analytics(user_id: int, days: int = 30) -> Optional[Dict]:
        """Get cached user feedback analytics."""
        key = CacheKeys.user_analytics(user_id, days)
        return cache.get(key)
    
    @staticmethod
    def set_user_feedback_analytics(user_id: int, data: Dict, days: int = 30, ttl: int = 1800):
        """Cache user feedback analytics."""
        key = CacheKeys.user_analytics(user_id, days)
        cache.set(key, data, ttl)
    
    @staticmethod
    def get_team_performance(team_id: str) -> Optional[Dict]:
        """Get cached team performance data."""
        key = CacheKeys.team_analytics(team_id)
        return cache.get(key)
    
    @staticmethod
    def set_team_performance(team_id: str, data: Dict, ttl: int = 3600):
        """Cache team performance data."""
        key = CacheKeys.team_analytics(team_id)
        cache.set(key, data, ttl)
    
    @staticmethod
    def invalidate_user_analytics(user_id: int):
        """Invalidate all user analytics cache."""
        pattern = f"analytics:user:{user_id}:*"
        cache.delete_pattern(pattern)
    
    @staticmethod
    def invalidate_team_analytics(team_id: str):
        """Invalidate team analytics cache."""
        key = CacheKeys.team_analytics(team_id)
        cache.delete(key)


class GitHubCache:
    """Specialized caching for GitHub integration data."""
    
    @staticmethod
    def get_repo_stats(repo_id: str) -> Optional[Dict]:
        """Get cached repository statistics."""
        key = CacheKeys.github_repo_stats(repo_id)
        return cache.get(key)
    
    @staticmethod
    def set_repo_stats(repo_id: str, stats: Dict, ttl: int = 1800):
        """Cache repository statistics."""
        key = CacheKeys.github_repo_stats(repo_id)
        cache.set(key, stats, ttl)
    
    @staticmethod
    def get_pr_analysis(pr_id: str) -> Optional[Dict]:
        """Get cached PR analysis results."""
        key = CacheKeys.pr_analysis_results(pr_id)
        return cache.get(key)
    
    @staticmethod
    def set_pr_analysis(pr_id: str, analysis: Dict, ttl: int = 7200):
        """Cache PR analysis results."""
        key = CacheKeys.pr_analysis_results(pr_id)
        cache.set(key, analysis, ttl)
    
    @staticmethod
    def invalidate_repo_cache(repo_id: str):
        """Invalidate all cache for a repository."""
        patterns = [
            f"github:repo:{repo_id}:*",
            f"pr:analysis:*:repo:{repo_id}:*"
        ]
        for pattern in patterns:
            cache.delete_pattern(pattern)


class UserCache:
    """Specialized caching for user data."""
    
    @staticmethod
    def get_profile(user_id: int) -> Optional[Dict]:
        """Get cached user profile."""
        key = CacheKeys.user_profile(user_id)
        return cache.get(key)
    
    @staticmethod
    def set_profile(user_id: int, profile: Dict, ttl: int = 3600):
        """Cache user profile."""
        key = CacheKeys.user_profile(user_id)
        cache.set(key, profile, ttl)
    
    @staticmethod
    def invalidate_profile(user_id: int):
        """Invalidate user profile cache."""
        key = CacheKeys.user_profile(user_id)
        cache.delete(key)


class RateLimitCache:
    """Rate limiting using Redis."""
    
    @staticmethod
    def check_rate_limit(user_id: int, endpoint: str, limit: int, window: int = 3600) -> bool:
        """Check if user has exceeded rate limit."""
        key = CacheKeys.rate_limit(user_id, endpoint)
        current = cache.increment(key, 1, window)
        return current is not None and current <= limit
    
    @staticmethod
    def get_rate_limit_status(user_id: int, endpoint: str) -> Optional[int]:
        """Get current rate limit count."""
        key = CacheKeys.rate_limit(user_id, endpoint)
        return cache.get(key)


class SessionCache:
    """Session management using Redis."""
    
    @staticmethod
    def set_session(session_id: str, data: Dict, ttl: int = 86400):
        """Store session data."""
        key = CacheKeys.session_data(session_id)
        cache.set(key, data, ttl)
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict]:
        """Get session data."""
        key = CacheKeys.session_data(session_id)
        return cache.get(key)
    
    @staticmethod
    def delete_session(session_id: str):
        """Delete session data."""
        key = CacheKeys.session_data(session_id)
        cache.delete(key)


# Cache warming utilities
class CacheWarmer:
    """Utilities to pre-warm frequently accessed cache entries."""
    
    @staticmethod
    async def warm_user_analytics(user_ids: List[int]):
        """Pre-warm user analytics cache."""
        from app.services.analytics_service import AnalyticsService
        
        analytics_service = AnalyticsService()
        for user_id in user_ids:
            try:
                # Warm different time periods
                for days in [7, 30, 90]:
                    analytics_data = await analytics_service.get_user_feedback_analytics(user_id, days)
                    AnalyticsCache.set_user_feedback_analytics(user_id, analytics_data, days)
                logger.info(f"Warmed analytics cache for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to warm cache for user {user_id}: {e}")
    
    @staticmethod
    async def warm_github_stats(repo_ids: List[str]):
        """Pre-warm GitHub repository statistics."""
        from app.services.github_service import GitHubService
        
        github_service = GitHubService()
        for repo_id in repo_ids:
            try:
                stats = await github_service.get_repository_stats(repo_id)
                GitHubCache.set_repo_stats(repo_id, stats)
                logger.info(f"Warmed GitHub cache for repo {repo_id}")
            except Exception as e:
                logger.error(f"Failed to warm GitHub cache for repo {repo_id}: {e}")


# Health check for cache
def check_cache_health() -> Dict[str, Any]:
    """Check Redis cache health and performance."""
    try:
        start_time = datetime.now()
        
        # Test basic operations
        test_key = "health_check_test"
        test_value = {"timestamp": start_time.isoformat()}
        
        # Test set/get
        cache.set(test_key, test_value, 60)
        retrieved = cache.get(test_key)
        cache.delete(test_key)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        # Get Redis info
        info = cache.redis_client.info()
        
        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }