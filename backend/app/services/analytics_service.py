"""
Analytics service for generating insights and statistics from feedback data.

This service handles:
- Acceptance rates and rejection patterns analysis
- Usage statistics and trends
- Real-time analytics data aggregation
- Performance metrics and caching

Requirements covered: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, text
from collections import defaultdict, Counter
import json
import redis
from app.models.feedback import FeedbackRecord, Issue, ModelVersion
from app.models.enhanced_feedback import EnhancedFeedback, FeedbackAction
from app.models.users import User
from app.schemas.feedback import DateRange
from app.core.analytics_config import analytics_config
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service class for generating analytics and insights from feedback data."""
    
    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis_client = redis_client
        self.cache_ttl = analytics_config.DEFAULT_CACHE_TTL
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from prefix and parameters."""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if available."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    def _set_cached_data(self, cache_key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set data in cache."""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(
                cache_key, 
                ttl or self.cache_ttl, 
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    async def get_acceptance_rates(
        self, 
        user_id: Optional[int] = None, 
        timeframe: str = "30d",
        pattern_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get acceptance rates for AI suggestions.
        
        Args:
            user_id: Optional filter by specific user
            timeframe: Time period (7d, 30d, 90d, 1y)
            pattern_type: Optional filter by pattern type
            
        Returns:
            Dict containing acceptance rate data
            
        Requirements: 2.1, 2.2
        """
        cache_key = self._get_cache_key(
            "acceptance_rates", 
            user_id=user_id, 
            timeframe=timeframe, 
            pattern_type=pattern_type
        )
        
        # Try to get from cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Calculate date range
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(timeframe, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query for enhanced feedback
        query = self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.timestamp >= start_date
        )
        
        if user_id:
            query = query.filter(EnhancedFeedback.user_id == user_id)
        
        if pattern_type:
            query = query.filter(EnhancedFeedback.suggestion_type == pattern_type)
        
        feedback_records = query.all()
        
        if not feedback_records:
            result = {
                "total_feedback": 0,
                "acceptance_rate": 0.0,
                "rejection_rate": 0.0,
                "daily_rates": {},
                "pattern_breakdown": {},
                "timeframe": timeframe
            }
        else:
            # Calculate overall rates
            total_count = len(feedback_records)
            accept_count = sum(1 for f in feedback_records if f.action == FeedbackAction.ACCEPT)
            reject_count = sum(1 for f in feedback_records if f.action == FeedbackAction.REJECT)
            
            acceptance_rate = (accept_count / total_count) * 100 if total_count > 0 else 0
            rejection_rate = (reject_count / total_count) * 100 if total_count > 0 else 0
            
            # Calculate daily rates
            daily_rates = self._calculate_daily_acceptance_rates(feedback_records)
            
            # Calculate pattern breakdown
            pattern_breakdown = self._calculate_pattern_acceptance_rates(feedback_records)
            
            result = {
                "total_feedback": total_count,
                "acceptance_rate": round(acceptance_rate, 2),
                "rejection_rate": round(rejection_rate, 2),
                "daily_rates": daily_rates,
                "pattern_breakdown": pattern_breakdown,
                "timeframe": timeframe
            }
        
        # Cache the result
        self._set_cached_data(cache_key, result)
        
        return result
    
    def _calculate_daily_acceptance_rates(self, feedback_records: List[EnhancedFeedback]) -> Dict[str, float]:
        """Calculate daily acceptance rates from feedback records."""
        daily_feedback = defaultdict(lambda: {"accept": 0, "reject": 0, "total": 0})
        
        for record in feedback_records:
            date_str = record.timestamp.strftime('%Y-%m-%d')
            daily_feedback[date_str]["total"] += 1
            if record.action == FeedbackAction.ACCEPT:
                daily_feedback[date_str]["accept"] += 1
            elif record.action == FeedbackAction.REJECT:
                daily_feedback[date_str]["reject"] += 1
        
        daily_rates = {}
        for date_str, counts in daily_feedback.items():
            if counts["total"] > 0:
                daily_rates[date_str] = round((counts["accept"] / counts["total"]) * 100, 2)
        
        return daily_rates
    
    def _calculate_pattern_acceptance_rates(self, feedback_records: List[EnhancedFeedback]) -> Dict[str, Dict[str, Any]]:
        """Calculate acceptance rates by pattern type."""
        pattern_feedback = defaultdict(lambda: {"accept": 0, "reject": 0, "total": 0})
        
        for record in feedback_records:
            pattern = record.suggestion_type or "unknown"
            pattern_feedback[pattern]["total"] += 1
            if record.action == FeedbackAction.ACCEPT:
                pattern_feedback[pattern]["accept"] += 1
            elif record.action == FeedbackAction.REJECT:
                pattern_feedback[pattern]["reject"] += 1
        
        pattern_breakdown = {}
        for pattern, counts in pattern_feedback.items():
            if counts["total"] > 0:
                acceptance_rate = (counts["accept"] / counts["total"]) * 100
                pattern_breakdown[pattern] = {
                    "acceptance_rate": round(acceptance_rate, 2),
                    "total_feedback": counts["total"],
                    "accept_count": counts["accept"],
                    "reject_count": counts["reject"]
                }
        
        return pattern_breakdown
    
    async def get_rejection_patterns(
        self, 
        user_id: Optional[int] = None,
        timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """
        Analyze rejection patterns and reasons.
        
        Args:
            user_id: Optional filter by specific user
            timeframe: Time period for analysis
            
        Returns:
            Dict containing rejection pattern analysis
            
        Requirements: 2.2, 2.3
        """
        cache_key = self._get_cache_key(
            "rejection_patterns", 
            user_id=user_id, 
            timeframe=timeframe
        )
        
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Calculate date range
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(timeframe, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query rejected feedback with reasons
        query = self.db.query(EnhancedFeedback).filter(
            and_(
                EnhancedFeedback.action == FeedbackAction.REJECT,
                EnhancedFeedback.timestamp >= start_date
            )
        )
        
        if user_id:
            query = query.filter(EnhancedFeedback.user_id == user_id)
        
        rejected_feedback = query.all()
        
        if not rejected_feedback:
            result = {
                "total_rejections": 0,
                "rejection_reasons": {},
                "custom_reasons": [],
                "pattern_rejections": {},
                "timeframe": timeframe
            }
        else:
            # Analyze rejection reasons
            rejection_reasons = Counter()
            custom_reasons = []
            pattern_rejections = defaultdict(int)
            
            for feedback in rejected_feedback:
                # Count predefined rejection reasons
                if feedback.rejection_reasons:
                    for reason in feedback.rejection_reasons:
                        rejection_reasons[reason] += 1
                
                # Collect custom reasons
                if feedback.custom_reason:
                    custom_reasons.append(feedback.custom_reason)
                
                # Count rejections by pattern type
                pattern = feedback.suggestion_type or "unknown"
                pattern_rejections[pattern] += 1
            
            result = {
                "total_rejections": len(rejected_feedback),
                "rejection_reasons": dict(rejection_reasons),
                "custom_reasons": custom_reasons[-50:],  # Last 50 custom reasons
                "pattern_rejections": dict(pattern_rejections),
                "timeframe": timeframe
            }
        
        # Cache the result
        self._set_cached_data(cache_key, result)
        
        return result
    
    async def get_usage_statistics(
        self, 
        user_id: Optional[int] = None,
        timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get usage statistics and activity metrics.
        
        Args:
            user_id: Optional filter by specific user
            timeframe: Time period for analysis
            
        Returns:
            Dict containing usage statistics
            
        Requirements: 2.3, 2.4
        """
        cache_key = self._get_cache_key(
            "usage_statistics", 
            user_id=user_id, 
            timeframe=timeframe
        )
        
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Calculate date range
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(timeframe, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query feedback data
        feedback_query = self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.timestamp >= start_date
        )
        
        if user_id:
            feedback_query = feedback_query.filter(EnhancedFeedback.user_id == user_id)
        
        feedback_records = feedback_query.all()
        
        # Calculate statistics
        total_interactions = len(feedback_records)
        unique_users = len(set(f.user_id for f in feedback_records)) if not user_id else 1
        
        # Daily activity
        daily_activity = defaultdict(int)
        for record in feedback_records:
            date_str = record.timestamp.strftime('%Y-%m-%d')
            daily_activity[date_str] += 1
        
        # Most active users (if not filtering by user)
        most_active_users = {}
        if not user_id:
            user_activity = Counter(f.user_id for f in feedback_records)
            most_active_users = dict(user_activity.most_common(10))
        
        # Suggestion types usage
        suggestion_types = Counter(f.suggestion_type or "unknown" for f in feedback_records)
        
        result = {
            "total_interactions": total_interactions,
            "unique_users": unique_users,
            "daily_activity": dict(daily_activity),
            "most_active_users": most_active_users,
            "suggestion_types_usage": dict(suggestion_types),
            "average_daily_interactions": round(total_interactions / days, 2) if days > 0 else 0,
            "timeframe": timeframe
        }
        
        # Cache the result
        self._set_cached_data(cache_key, result)
        
        return result
    
    async def get_learning_progress(self) -> Dict[str, Any]:
        """
        Get AI model learning progress indicators.
        
        Returns:
            Dict containing learning progress metrics
            
        Requirements: 2.4, 2.5
        """
        cache_key = "learning_progress"
        
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Get model versions and their performance
        model_versions = self.db.query(ModelVersion).order_by(desc(ModelVersion.created_at)).limit(10).all()
        
        # Calculate improvement trends
        version_performance = []
        for version in model_versions:
            version_performance.append({
                "version": version.version_name,
                "accuracy": version.accuracy_score,
                "acceptance_rate": version.acceptance_rate,
                "created_at": version.created_at.isoformat() if version.created_at else None,
                "is_active": version.is_active
            })
        
        # Get recent feedback trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_feedback = self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.timestamp >= thirty_days_ago
        ).all()
        
        # Calculate learning indicators
        total_recent_feedback = len(recent_feedback)
        recent_acceptance_rate = 0
        if total_recent_feedback > 0:
            recent_accepts = sum(1 for f in recent_feedback if f.action == FeedbackAction.ACCEPT)
            recent_acceptance_rate = (recent_accepts / total_recent_feedback) * 100
        
        # Training data availability
        training_data_count = self.db.query(FeedbackRecord).filter(
            FeedbackRecord.is_validated == True
        ).count()
        
        result = {
            "model_versions": version_performance,
            "recent_acceptance_rate": round(recent_acceptance_rate, 2),
            "total_training_data": training_data_count,
            "recent_feedback_count": total_recent_feedback,
            "learning_indicators": {
                "data_quality": "good" if training_data_count > 1000 else "needs_improvement",
                "feedback_volume": "high" if total_recent_feedback > 100 else "low",
                "model_performance": "improving" if recent_acceptance_rate > 70 else "stable"
            }
        }
        
        # Cache the result with longer TTL for model data
        self._set_cached_data(cache_key, result, ttl=analytics_config.LEARNING_PROGRESS_CACHE_TTL)
        
        return result
    
    async def get_analytics_dashboard_data(
        self, 
        user_id: Optional[int] = None,
        timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics data for dashboard display.
        
        Args:
            user_id: Optional filter by specific user
            timeframe: Time period for analysis
            
        Returns:
            Dict containing all dashboard analytics data
            
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
        """
        # Get all analytics components
        acceptance_rates = await self.get_acceptance_rates(user_id, timeframe)
        rejection_patterns = await self.get_rejection_patterns(user_id, timeframe)
        usage_statistics = await self.get_usage_statistics(user_id, timeframe)
        learning_progress = await self.get_learning_progress()
        
        return {
            "acceptance_rates": acceptance_rates,
            "rejection_patterns": rejection_patterns,
            "usage_statistics": usage_statistics,
            "learning_progress": learning_progress,
            "generated_at": datetime.utcnow().isoformat(),
            "timeframe": timeframe,
            "user_id": user_id
        }
    
    async def export_analytics_data(
        self,
        export_format: str = "json",
        date_range: Optional[DateRange] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Export analytics data in specified format.
        
        Args:
            export_format: Format for export (json, csv)
            date_range: Optional date range filter
            user_id: Optional user filter
            
        Returns:
            Dict containing export data and metadata
            
        Requirements: 2.5
        """
        # Build query based on filters
        query = self.db.query(EnhancedFeedback)
        
        if date_range:
            query = query.filter(
                and_(
                    EnhancedFeedback.timestamp >= date_range.start_date,
                    EnhancedFeedback.timestamp <= date_range.end_date
                )
            )
        
        if user_id:
            query = query.filter(EnhancedFeedback.user_id == user_id)
        
        feedback_records = query.all()
        
        # Prepare export data
        export_data = []
        for record in feedback_records:
            export_data.append({
                "id": record.id,
                "suggestion_id": record.suggestion_id,
                "user_id": record.user_id,
                "action": record.action.value,
                "rejection_reasons": record.rejection_reasons,
                "custom_reason": record.custom_reason,
                "suggestion_type": record.suggestion_type,
                "confidence_score": record.confidence_score,
                "timestamp": record.timestamp.isoformat(),
                "context_data": record.context_data
            })
        
        return {
            "data": export_data,
            "format": export_format,
            "total_records": len(export_data),
            "exported_at": datetime.utcnow().isoformat(),
            "filters": {
                "date_range": {
                    "start": date_range.start_date.isoformat() if date_range else None,
                    "end": date_range.end_date.isoformat() if date_range else None
                } if date_range else None,
                "user_id": user_id
            }
        }
    
    def invalidate_cache(self, pattern: str = "*") -> None:
        """
        Invalidate cached analytics data.
        
        Args:
            pattern: Cache key pattern to invalidate
        """
        if not self.redis_client:
            return
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")