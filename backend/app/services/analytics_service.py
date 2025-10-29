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
from ..models import User, Feedback, EnhancedFeedback, FeedbackAction
from ..models.feedback import ModelVersion, FeedbackRecord, Issue
from ..schemas.feedback import FeedbackCreate, DateRange
from ..core.config import settings
from ..core.analytics_config import analytics_config
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
    
    async def get_dashboard_data(self, user_id: int, timeframe: str = "30d") -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for a user including all metrics.
        
        Args:
            user_id: User ID to get dashboard data for
            timeframe: Time period (7d, 30d, 90d, 1y)
            
        Returns:
            Dict containing all dashboard analytics data
            
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
        """
        cache_key = self._get_cache_key("dashboard_data", user_id=user_id, timeframe=timeframe)
        
        # Try to get from cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Cache hit for dashboard data: user {user_id}, timeframe {timeframe}")
            return cached_data
        
        try:
            # Get all dashboard components concurrently
            user_stats = await self.get_user_stats(user_id)
            usage_trends = await self.get_usage_trends(user_id, timeframe)
            feedback_distribution = await self.get_feedback_distribution(user_id, timeframe)
            
            # Calculate performance metrics
            performance_metrics = await self._calculate_performance_metrics(user_id, timeframe)
            
            result = {
                "userStats": user_stats,
                "usageTrends": usage_trends,
                "feedbackDistribution": feedback_distribution,
                "performanceMetrics": performance_metrics,
                "generatedAt": datetime.utcnow().isoformat(),
                "timeframe": timeframe,
                "userId": user_id
            }
            
            # Cache the result with shorter TTL for dashboard
            self._set_cached_data(cache_key, result, ttl=analytics_config.DASHBOARD_CACHE_TTL)
            logger.info(f"Dashboard data calculated and cached for user {user_id}, timeframe {timeframe}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating dashboard data for user {user_id}: {e}")
            return {
                "userStats": {"totalReviews": 0, "totalAnalyses": 0, "successRate": 0.0, "totalFeedback": 0, "acceptanceRate": 0.0, "recentActivity": []},
                "usageTrends": {"trends": [], "timeframe": timeframe, "summary": {"totalReviews": 0, "totalFeedback": 0, "avgDailyReviews": 0.0}},
                "feedbackDistribution": {"distribution": {"accept": 0, "reject": 0, "modify": 0, "ignore": 0}, "timeframe": timeframe, "total": 0},
                "performanceMetrics": {"avgResponseTime": 0.0, "avgIssuesPerReview": 0.0, "mostCommonPatterns": [], "improvementTrend": "stable"},
                "generatedAt": datetime.utcnow().isoformat(),
                "timeframe": timeframe,
                "userId": user_id
            }
    
    async def _calculate_performance_metrics(self, user_id: int, timeframe: str = "30d") -> Dict[str, Any]:
        """
        Calculate performance metrics for a user.
        
        Args:
            user_id: User ID to calculate metrics for
            timeframe: Time period for calculation
            
        Returns:
            Dict containing performance metrics
        """
        from ..models.analysis import DirectAnalysis
        from ..models.feedback import Issue
        
        try:
            # Calculate date range
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(timeframe, 30)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get completed analyses in timeframe
            analyses = self.db.query(DirectAnalysis).filter(
                and_(
                    DirectAnalysis.user_id == user_id,
                    DirectAnalysis.status == "completed",
                    DirectAnalysis.created_at >= start_date
                )
            ).all()
            
            if not analyses:
                return {
                    "avgResponseTime": 0.0,
                    "avgIssuesPerReview": 0.0,
                    "mostCommonPatterns": [],
                    "improvementTrend": "stable",
                    "totalAnalysisTime": 0.0,
                    "avgComplexityScore": 0.0
                }
            
            # Calculate average response time (analysis duration)
            response_times = []
            total_issues = 0
            complexity_scores = []
            
            for analysis in analyses:
                if analysis.completed_at and analysis.created_at:
                    duration = (analysis.completed_at - analysis.created_at).total_seconds()
                    response_times.append(duration)
                
                total_issues += analysis.issues_count or 0
                
                if analysis.complexity_score:
                    complexity_scores.append(analysis.complexity_score)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            avg_issues_per_review = total_issues / len(analyses) if analyses else 0.0
            avg_complexity_score = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0.0
            
            # Get most common patterns from issues
            issues = self.db.query(Issue).join(DirectAnalysis).filter(
                and_(
                    DirectAnalysis.user_id == user_id,
                    DirectAnalysis.created_at >= start_date
                )
            ).all()
            
            pattern_counts = Counter(issue.pattern_type for issue in issues)
            most_common_patterns = [
                {"pattern": pattern, "count": count}
                for pattern, count in pattern_counts.most_common(5)
            ]
            
            # Calculate improvement trend (compare with previous period)
            prev_start_date = start_date - timedelta(days=days)
            prev_analyses = self.db.query(DirectAnalysis).filter(
                and_(
                    DirectAnalysis.user_id == user_id,
                    DirectAnalysis.status == "completed",
                    DirectAnalysis.created_at >= prev_start_date,
                    DirectAnalysis.created_at < start_date
                )
            ).count()
            
            current_count = len(analyses)
            if prev_analyses > 0:
                if current_count > prev_analyses:
                    improvement_trend = "improving"
                elif current_count < prev_analyses:
                    improvement_trend = "declining"
                else:
                    improvement_trend = "stable"
            else:
                improvement_trend = "new" if current_count > 0 else "stable"
            
            return {
                "avgResponseTime": round(avg_response_time, 2),
                "avgIssuesPerReview": round(avg_issues_per_review, 2),
                "mostCommonPatterns": most_common_patterns,
                "improvementTrend": improvement_trend,
                "totalAnalysisTime": round(sum(response_times), 2),
                "avgComplexityScore": round(avg_complexity_score, 2),
                "totalAnalyses": len(analyses),
                "totalIssuesFound": total_issues
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics for user {user_id}: {e}")
            return {
                "avgResponseTime": 0.0,
                "avgIssuesPerReview": 0.0,
                "mostCommonPatterns": [],
                "improvementTrend": "stable",
                "totalAnalysisTime": 0.0,
                "avgComplexityScore": 0.0
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
    
    def invalidate_user_cache(self, user_id: int) -> None:
        """
        Invalidate all cached data for a specific user.
        
        Args:
            user_id: User ID to invalidate cache for
        """
        patterns = [
            f"user_stats:user_id:{user_id}",
            f"usage_trends:user_id:{user_id}:*",
            f"usage_trends:timeframe:*:user_id:{user_id}",
            f"usage_trends_v2:user_id:{user_id}:*",
            f"usage_trends_v2:timeframe:*:user_id:{user_id}",
            f"feedback_distribution:user_id:{user_id}:*",
            f"issue_trends:user_id:{user_id}:*",
            f"issue_trends:timeframe:*:user_id:{user_id}",
            f"criticality_distribution:user_id:{user_id}:*",
            f"criticality_distribution:timeframe:*:user_id:{user_id}",
            f"dashboard_data:user_id:{user_id}:*"
        ]
        
        for pattern in patterns:
            self.invalidate_cache(pattern)
        
        logger.info(f"Invalidated all cache for user: {user_id}")
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get user statistics including total reviews, analyses, success rate, and recent activity.
        
        Args:
            user_id: User ID to get statistics for
            
        Returns:
            Dict containing user statistics
            
        Requirements: 1.1, 1.3, 1.4, 1.5, 1.6
        """
        from ..models.analysis import DirectAnalysis
        from ..models.feedback import Issue
        
        cache_key = self._get_cache_key("user_stats", user_id=user_id)
        
        # Try to get from cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            has_performance = bool(cached_data.get("performanceMetrics"))
            meets_expectations = has_performance or cached_data.get("totalReviews", 0) == 0
            if meets_expectations:
                logger.info(f"Cache hit for user stats: {user_id}")
                return cached_data
            logger.warning(
                "Stale cache detected for user %s; recomputing analytics to refresh performance metrics",
                user_id
            )
        
        try:
            # Get total analyses count
            total_analyses = self.db.query(DirectAnalysis).filter(
                DirectAnalysis.user_id == user_id
            ).count()
            
            # Get completed analyses
            completed_analyses = self.db.query(DirectAnalysis).filter(
                and_(
                    DirectAnalysis.user_id == user_id,
                    DirectAnalysis.status == "completed"
                )
            ).count()
            
            # Calculate success rate
            success_rate = (completed_analyses / total_analyses * 100) if total_analyses > 0 else 0
            
            # Get total feedback count
            total_feedback = self.db.query(FeedbackRecord).filter(
                FeedbackRecord.user_id == user_id
            ).count()
            
            # Get accepted feedback count
            accepted_feedback = self.db.query(FeedbackRecord).filter(
                and_(
                    FeedbackRecord.user_id == user_id,
                    FeedbackRecord.feedback_type == "accept"
                )
            ).count()
            
            # Calculate acceptance rate
            acceptance_rate = (accepted_feedback / total_feedback * 100) if total_feedback > 0 else 0
            
            # Get total issues found across all analyses
            total_issues = (
                self.db.query(func.count(Issue.id))
                .join(DirectAnalysis, DirectAnalysis.id == Issue.analysis_id)
                .filter(DirectAnalysis.user_id == user_id)
                .scalar()
                or 0
            )

            if total_issues == 0:
                denormalized_issue_count = (
                    self.db.query(func.coalesce(func.sum(DirectAnalysis.issues_count), 0))
                    .filter(DirectAnalysis.user_id == user_id)
                    .scalar()
                    or 0
                )
                total_issues = int(denormalized_issue_count)
            
            # Get recent activity (last 10 analyses)
            recent_analyses = self.db.query(DirectAnalysis).filter(
                DirectAnalysis.user_id == user_id
            ).order_by(desc(DirectAnalysis.created_at)).limit(10).all()
            
            recent_activity = []
            for analysis in recent_analyses:
                activity_type = "review"
                status_map = {
                    "completed": "success",
                    "failed": "warning",
                    "pending": "info",
                    "in_progress": "info"
                }
                
                # Get issue count for this analysis
                issue_count = analysis.issues_count or 0
                description = f"Analyzed {analysis.language} code"
                if issue_count > 0:
                    description += f" - {issue_count} issues found"
                description += f" - {analysis.status}"
                
                recent_activity.append({
                    "id": analysis.id,
                    "type": activity_type,
                    "description": description,
                    "time": analysis.created_at.isoformat() if analysis.created_at else None,
                    "status": status_map.get(analysis.status, "info"),
                    "issuesFound": issue_count
                })

            # Build performance metrics for recent period (default 30 days)
            metrics_window_days = 30
            metrics_start = datetime.utcnow() - timedelta(days=metrics_window_days)
            use_all_time_window = False

            meaningful_status_filter = or_(
                DirectAnalysis.status == "completed",
                DirectAnalysis.completed_at.isnot(None),
                DirectAnalysis.results.isnot(None)
            )

            recent_completed_analyses = (
                self.db.query(DirectAnalysis)
                .filter(
                    DirectAnalysis.user_id == user_id,
                    DirectAnalysis.created_at >= metrics_start,
                    meaningful_status_filter
                )
                .order_by(desc(DirectAnalysis.created_at))
                .all()
            )

            if not recent_completed_analyses:
                recent_completed_analyses = (
                    self.db.query(DirectAnalysis)
                    .filter(
                        DirectAnalysis.user_id == user_id,
                        meaningful_status_filter
                    )
                    .order_by(desc(DirectAnalysis.created_at))
                    .limit(200)
                    .all()
                )

                if recent_completed_analyses:
                    use_all_time_window = True
                    metrics_start = None  # Indicates all-time window

            performance_metrics: List[Dict[str, Any]] = []
            performance_summary: Dict[str, Any]

            if recent_completed_analyses:
                def _resolve_response_duration_seconds(analysis: DirectAnalysis) -> Optional[float]:
                    """Prefer completed_at delta, fall back to stored processing time metrics."""
                    if analysis.completed_at and analysis.created_at:
                        delta = (analysis.completed_at - analysis.created_at).total_seconds()
                        if delta >= 0:
                            return delta
                    if analysis.ast_processing_time and analysis.ast_processing_time > 0:
                        return float(analysis.ast_processing_time)
                    if isinstance(analysis.results, dict):
                        # Look for common timing fields recorded in analysis results payloads
                        candidate_dicts = [analysis.results]
                        candidate_dicts.extend(
                            value for value in analysis.results.values() if isinstance(value, dict)
                        )
                        timing_keys = ("processing_time_seconds", "processingTimeSeconds", "processing_time")
                        for payload in candidate_dicts:
                            for key in timing_keys:
                                value = payload.get(key) if isinstance(payload, dict) else None
                                if isinstance(value, (int, float)) and value >= 0:
                                    return float(value)
                    return None

                response_durations = [
                    duration for analysis in recent_completed_analyses
                    if (duration := _resolve_response_duration_seconds(analysis)) is not None
                ]
                avg_response_time = sum(response_durations) / len(response_durations) if response_durations else 0.0

                total_issues_period = sum((analysis.issues_count or 0) for analysis in recent_completed_analyses)
                avg_issues_per_review = total_issues_period / len(recent_completed_analyses) if recent_completed_analyses else 0.0

                feedback_filters = [FeedbackRecord.user_id == user_id]
                if not use_all_time_window and metrics_start is not None:
                    feedback_filters.append(FeedbackRecord.created_at >= metrics_start)

                recent_feedback_total = self.db.query(func.count(FeedbackRecord.id)).filter(
                    *feedback_filters
                ).scalar() or 0
                recent_feedback_accept = self.db.query(func.count(FeedbackRecord.id)).filter(
                    *feedback_filters,
                    FeedbackRecord.feedback_type == "accept"
                ).scalar() or 0
                accuracy_recent = (
                    (recent_feedback_accept / recent_feedback_total) * 100
                    if recent_feedback_total > 0 else acceptance_rate
                )

                # Track common patterns surfaced during the window
                issue_filters = [DirectAnalysis.user_id == user_id, meaningful_status_filter]
                if not use_all_time_window and metrics_start is not None:
                    issue_filters.append(DirectAnalysis.created_at >= metrics_start)

                recent_issues = (
                    self.db.query(Issue)
                    .join(DirectAnalysis, DirectAnalysis.id == Issue.analysis_id)
                    .filter(*issue_filters)
                    .all()
                )
                pattern_counts = Counter(issue.pattern_type for issue in recent_issues if issue.pattern_type)
                top_patterns = [
                    {"pattern": pattern, "count": count}
                    for pattern, count in pattern_counts.most_common(5)
                ]

                # Compare with previous window to show directional trend
                response_trend = "stable"
                if not use_all_time_window and metrics_start is not None:
                    previous_window_start = metrics_start - timedelta(days=metrics_window_days)
                    previous_completed = (
                        self.db.query(DirectAnalysis)
                        .filter(
                            DirectAnalysis.user_id == user_id,
                            DirectAnalysis.created_at >= previous_window_start,
                            DirectAnalysis.created_at < metrics_start,
                            meaningful_status_filter
                        )
                        .all()
                    )
                    previous_durations = [
                        duration for analysis in previous_completed
                        if (duration := _resolve_response_duration_seconds(analysis)) is not None
                    ]
                    prev_avg_response = sum(previous_durations) / len(previous_durations) if previous_durations else None
                    if prev_avg_response is not None:
                        if avg_response_time < prev_avg_response:
                            response_trend = "improving"
                        elif avg_response_time > prev_avg_response:
                            response_trend = "regressing"

                period_label = (
                    "All time" if use_all_time_window
                    else f"Last {metrics_window_days} days"
                )

                performance_metrics.append({
                    "period": period_label,
                    "avgResponseTime": round(avg_response_time, 2),
                    "avgIssuesPerReview": round(avg_issues_per_review, 2),
                    "accuracy": round(accuracy_recent or 0.0, 2),
                    "totalReviews": len(recent_completed_analyses),
                    "topPatterns": top_patterns,
                    "responseTrend": response_trend
                })

                performance_summary = {
                    "window": metrics_window_days if not use_all_time_window else None,
                    "reviews": len(recent_completed_analyses),
                    "avgResponseTime": round(avg_response_time, 2),
                    "avgIssuesPerReview": round(avg_issues_per_review, 2),
                    "accuracy": round(accuracy_recent or 0.0, 2)
                }
            else:
                performance_metrics = []
                performance_summary = {
                    "window": metrics_window_days,
                    "reviews": 0,
                    "avgResponseTime": 0.0,
                    "avgIssuesPerReview": 0.0,
                    "accuracy": 0.0
                }
            
            result = {
                # Legacy keys kept for compatibility
                "totalReviews": total_analyses,
                "totalAnalyses": completed_analyses,
                # Explicit, clearer keys for frontend mapping
                "filesAnalyzed": total_analyses,
                "completedAnalyses": completed_analyses,
                "successRate": round(success_rate, 2),
                "totalFeedback": total_feedback,
                "acceptanceRate": round(acceptance_rate, 2),
                "totalIssuesFound": total_issues,
                "recentActivity": recent_activity,
                "performanceMetrics": performance_metrics,
                "performanceSummary": performance_summary
            }
            
            # Cache the result with shorter TTL for real-time feel
            self._set_cached_data(cache_key, result, ttl=analytics_config.DASHBOARD_CACHE_TTL)
            logger.info(f"User stats calculated and cached for user: {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating user stats for user {user_id}: {e}")
            # Return empty stats on error
            return {
                "totalReviews": 0,
                "totalAnalyses": 0,
                "successRate": 0.0,
                "totalFeedback": 0,
                "acceptanceRate": 0.0,
                "totalIssuesFound": 0,
                "recentActivity": [],
                "performanceMetrics": [],
                "performanceSummary": {
                    "window": 30,
                    "reviews": 0,
                    "avgResponseTime": 0.0,
                    "avgIssuesPerReview": 0.0,
                    "accuracy": 0.0
                }
            }
    
    async def get_usage_trends(self, user_id: int, timeframe: str = "30d") -> Dict[str, Any]:
        """
        Get usage trends over time for a specific user.
        
        Args:
            user_id: User ID to get trends for
            timeframe: Time period (7d, 30d, 90d, 1y)
            
        Returns:
            Dict containing usage trends data
            
        Requirements: 1.3, 1.4, 1.5
        """
        from ..models.analysis import DirectAnalysis

        cache_key = self._get_cache_key("usage_trends_v2", user_id=user_id, timeframe=timeframe)
        
        # Try to get from cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Cache hit for usage trends: user {user_id}, timeframe {timeframe}")
            return cached_data
        
        try:
            # Calculate date range
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(timeframe, 30)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get analyses in timeframe with optimized query
            analyses = self.db.query(DirectAnalysis).filter(
                and_(
                    DirectAnalysis.user_id == user_id,
                    DirectAnalysis.created_at >= start_date
                )
            ).order_by(DirectAnalysis.created_at).all()
            
            # Get feedback in timeframe with optimized query
            feedback_records = self.db.query(FeedbackRecord).filter(
                and_(
                    FeedbackRecord.user_id == user_id,
                    FeedbackRecord.created_at >= start_date
                )
            ).order_by(FeedbackRecord.created_at).all()
            
            # Group by date with enhanced metrics
            daily_data = defaultdict(lambda: {
                "reviews": 0,
                "accepted": 0,
                "rejected": 0,
                "modified": 0,
                "issues_found": 0,
                "completed_reviews": 0
            })

            issues_by_date = {}
            if analyses:
                issue_counts = (
                    self.db.query(
                        func.date(DirectAnalysis.created_at).label("issue_date"),
                        func.count(Issue.id).label("issue_count")
                    )
                    .join(DirectAnalysis, Issue.analysis_id == DirectAnalysis.id)
                    .filter(
                        DirectAnalysis.user_id == user_id,
                        DirectAnalysis.created_at >= start_date
                    )
                    .group_by(func.date(DirectAnalysis.created_at))
                    .all()
                )

                for row in issue_counts:
                    date_value = row.issue_date
                    date_str = date_value.isoformat() if hasattr(date_value, "isoformat") else str(date_value)
                    issues_by_date[date_str] = int(row.issue_count or 0)
            
            for analysis in analyses:
                date_str = analysis.created_at.strftime('%Y-%m-%d')
                daily_data[date_str]["reviews"] += 1
                if analysis.status == "completed":
                    daily_data[date_str]["completed_reviews"] += 1
                if analysis.issues_count:
                    daily_data[date_str]["issues_found"] += analysis.issues_count

            for date_str, issue_count in issues_by_date.items():
                daily_data[date_str]["issues_found"] = issue_count
            
            for feedback in feedback_records:
                date_str = feedback.created_at.strftime('%Y-%m-%d')
                if feedback.feedback_type == "accept":
                    daily_data[date_str]["accepted"] += 1
                elif feedback.feedback_type == "reject":
                    daily_data[date_str]["rejected"] += 1
                elif feedback.feedback_type == "modify":
                    daily_data[date_str]["modified"] += 1
            
            # Fill in missing dates with zero values
            current_date = start_date.date()
            end_date = datetime.utcnow().date()
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                if date_str not in daily_data:
                    daily_data[date_str] = {
                        "reviews": 0, 
                        "accepted": 0, 
                        "rejected": 0, 
                        "modified": 0,
                        "issues_found": 0,
                        "completed_reviews": 0
                    }
                current_date += timedelta(days=1)
            
            # Convert to list format with enhanced data
            trends = []
            for date_str in sorted(daily_data.keys()):
                data = daily_data[date_str]
                trends.append({
                    "date": date_str,
                    "reviews": data["reviews"],
                    "accepted": data["accepted"],
                    "rejected": data["rejected"],
                    "modified": data["modified"],
                    "issuesFound": data["issues_found"],
                    "completedReviews": data["completed_reviews"]
                })
            
            # Calculate summary statistics
            total_reviews = sum(t["reviews"] for t in trends)
            total_feedback = sum(t["accepted"] + t["rejected"] + t["modified"] for t in trends)
            avg_daily_reviews = total_reviews / days if days > 0 else 0
            
            result = {
                "trends": trends,
                "timeframe": timeframe,
                "summary": {
                    "totalReviews": total_reviews,
                    "totalFeedback": total_feedback,
                    "avgDailyReviews": round(avg_daily_reviews, 2),
                    "totalIssuesFound": sum(t["issuesFound"] for t in trends)
                }
            }
            
            # Cache the result
            self._set_cached_data(cache_key, result, ttl=analytics_config.DEFAULT_CACHE_TTL)
            logger.info(f"Usage trends calculated and cached for user {user_id}, timeframe {timeframe}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating usage trends for user {user_id}: {e}")
            return {
                "trends": [],
                "timeframe": timeframe,
                "summary": {
                    "totalReviews": 0,
                    "totalFeedback": 0,
                    "avgDailyReviews": 0.0,
                    "totalIssuesFound": 0
                }
            }
    
    async def get_feedback_distribution(self, user_id: int, timeframe: str = "30d") -> Dict[str, Any]:
        """
        Get feedback distribution by type for a specific user.
        
        Args:
            user_id: User ID to get distribution for
            timeframe: Time period (7d, 30d, 90d, 1y)
            
        Returns:
            Dict containing feedback distribution data
            
        Requirements: 1.4, 1.5, 1.6
        """
        cache_key = self._get_cache_key("feedback_distribution", user_id=user_id, timeframe=timeframe)
        
        # Try to get from cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Cache hit for feedback distribution: user {user_id}, timeframe {timeframe}")
            return cached_data
        
        try:
            # Calculate date range
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(timeframe, 30)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get feedback in timeframe with optimized query
            feedback_records = self.db.query(FeedbackRecord).filter(
                and_(
                    FeedbackRecord.user_id == user_id,
                    FeedbackRecord.created_at >= start_date
                )
            ).all()
            
            # Count by type with enhanced categories
            distribution = {
                "accept": 0,
                "reject": 0,
                "modify": 0,
                "ignore": 0
            }
            
            # Track additional metrics
            severity_distribution = defaultdict(int)
            pattern_distribution = defaultdict(int)
            
            for feedback in feedback_records:
                feedback_type = feedback.feedback_type
                if feedback_type in distribution:
                    distribution[feedback_type] += 1
                
                # Get issue details for enhanced analytics
                if feedback.issue:
                    severity_distribution[feedback.issue.severity] += 1
                    pattern_distribution[feedback.issue.pattern_type] += 1
            
            # Calculate percentages
            total_feedback = sum(distribution.values())
            distribution_percentages = {}
            for feedback_type, count in distribution.items():
                percentage = (count / total_feedback * 100) if total_feedback > 0 else 0
                distribution_percentages[feedback_type] = round(percentage, 2)
            
            # Get top patterns and severities
            top_patterns = dict(Counter(pattern_distribution).most_common(5))
            top_severities = dict(Counter(severity_distribution).most_common(5))
            
            result = {
                "distribution": distribution,
                "distributionPercentages": distribution_percentages,
                "severityDistribution": dict(severity_distribution),
                "patternDistribution": dict(pattern_distribution),
                "topPatterns": top_patterns,
                "topSeverities": top_severities,
                "timeframe": timeframe,
                "total": total_feedback
            }
            
            # Cache the result
            self._set_cached_data(cache_key, result, ttl=analytics_config.DEFAULT_CACHE_TTL)
            logger.info(f"Feedback distribution calculated and cached for user {user_id}, timeframe {timeframe}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating feedback distribution for user {user_id}: {e}")
            return {
                "distribution": {"accept": 0, "reject": 0, "modify": 0, "ignore": 0},
                "distributionPercentages": {"accept": 0, "reject": 0, "modify": 0, "ignore": 0},
                "severityDistribution": {},
                "patternDistribution": {},
                "topPatterns": {},
                "topSeverities": {},
                "timeframe": timeframe,
                "total": 0
            }
    
    async def get_issue_trends(
        self,
        user_id: int,
        timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get issue trends over time for a specific user.
        
        Args:
            user_id: User ID to get trends for
            timeframe: Time period (7d, 30d, 90d, 1y)
            
        Returns:
            Dict containing time-series issue trend data
            
        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        from ..models.analysis import DirectAnalysis
        from ..models.feedback import Issue
        
        cache_key = self._get_cache_key("issue_trends", user_id=user_id, timeframe=timeframe)
        
        # Try to get from cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Cache hit for issue trends: user {user_id}, timeframe {timeframe}")
            return cached_data
        
        try:
            # Calculate date range
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(timeframe, 30)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get completed analyses in timeframe
            analyses = self.db.query(DirectAnalysis).filter(
                and_(
                    DirectAnalysis.user_id == user_id,
                    DirectAnalysis.status == "completed",
                    DirectAnalysis.created_at >= start_date
                )
            ).all()
            
            # Group issues by date and type
            daily_data = defaultdict(lambda: {
                "date": None,
                "errors": 0,
                "security_issues": 0,
                "warnings": 0,
                "total": 0
            })
            
            for analysis in analyses:
                date_str = analysis.created_at.strftime('%Y-%m-%d')
                daily_data[date_str]["date"] = date_str
                
                # Get issues for this analysis
                issues = self.db.query(Issue).filter(
                    Issue.analysis_id == analysis.id
                ).all()
                
                for issue in issues:
                    daily_data[date_str]["total"] += 1
                    
                    # Categorize by severity and type
                    severity = issue.severity.lower() if issue.severity else "unknown"
                    pattern_type = issue.pattern_type.lower() if issue.pattern_type else ""
                    
                    if severity in ["critical", "high", "error"]:
                        daily_data[date_str]["errors"] += 1
                    elif "security" in pattern_type or "vulnerability" in pattern_type:
                        daily_data[date_str]["security_issues"] += 1
                    elif severity in ["medium", "low", "warning"]:
                        daily_data[date_str]["warnings"] += 1
            
            # Convert to sorted list
            data_points = sorted(daily_data.values(), key=lambda x: x["date"])
            
            # Calculate summary statistics
            total_errors = sum(d["errors"] for d in data_points)
            total_security = sum(d["security_issues"] for d in data_points)
            total_warnings = sum(d["warnings"] for d in data_points)
            total_issues = sum(d["total"] for d in data_points)
            
            # Determine trend
            if len(data_points) >= 2:
                first_half = data_points[:len(data_points)//2]
                second_half = data_points[len(data_points)//2:]
                
                first_avg = sum(d["total"] for d in first_half) / len(first_half) if first_half else 0
                second_avg = sum(d["total"] for d in second_half) / len(second_half) if second_half else 0
                
                if second_avg < first_avg * 0.9:
                    trend = "improving"
                elif second_avg > first_avg * 1.1:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            result = {
                "timeframe": timeframe,
                "data_points": data_points,
                "summary": {
                    "total_errors": total_errors,
                    "total_security_issues": total_security,
                    "total_warnings": total_warnings,
                    "total_issues": total_issues,
                    "trend": trend
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            self._set_cached_data(cache_key, result)
            logger.info(f"Issue trends calculated and cached for user {user_id}, timeframe {timeframe}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating issue trends for user {user_id}: {e}", exc_info=True)
            return {
                "timeframe": timeframe,
                "data_points": [],
                "summary": {
                    "total_errors": 0,
                    "total_security_issues": 0,
                    "total_warnings": 0,
                    "total_issues": 0,
                    "trend": "unknown"
                },
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def get_criticality_distribution(
        self,
        user_id: int,
        timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get criticality/severity distribution of issues for a user.
        
        Args:
            user_id: User ID to get distribution for
            timeframe: Time period (7d, 30d, 90d, 1y)
            
        Returns:
            Dict containing severity distribution data
            
        Requirements: 5.1, 5.2, 5.3, 5.4
        """
        from ..models.analysis import DirectAnalysis
        from ..models.feedback import Issue
        
        cache_key = self._get_cache_key("criticality_distribution", user_id=user_id, timeframe=timeframe)
        
        # Try to get from cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Cache hit for criticality distribution: user {user_id}, timeframe {timeframe}")
            return cached_data
        
        try:
            # Calculate date range
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(timeframe, 30)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get issues for user's analyses in timeframe
            issues = self.db.query(Issue).join(DirectAnalysis).filter(
                and_(
                    DirectAnalysis.user_id == user_id,
                    DirectAnalysis.created_at >= start_date
                )
            ).all()
            
            # Categorize by severity
            distribution = {
                "severe": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
            
            for issue in issues:
                severity = issue.severity.lower() if issue.severity else "unknown"
                
                if severity in ["critical", "severe"]:
                    distribution["severe"] += 1
                elif severity == "high":
                    distribution["high"] += 1
                elif severity == "medium":
                    distribution["medium"] += 1
                elif severity == "low":
                    distribution["low"] += 1
            
            total_issues = len(issues)
            
            # Calculate percentages and add details
            distribution_with_details = {}
            for severity, count in distribution.items():
                percentage = (count / total_issues * 100) if total_issues > 0 else 0.0
                distribution_with_details[severity] = {
                    "count": count,
                    "percentage": round(percentage, 2)
                }
            
            # Get breakdown by issue type for each severity
            severity_breakdown = {}
            for severity in distribution.keys():
                severity_issues = [i for i in issues if i.severity and i.severity.lower() in self._get_severity_aliases(severity)]
                pattern_counts = Counter(i.pattern_type for i in severity_issues if i.pattern_type)
                severity_breakdown[severity] = dict(pattern_counts.most_common(5))
            
            result = {
                "timeframe": timeframe,
                "distribution": distribution_with_details,
                "total_issues": total_issues,
                "severity_breakdown": severity_breakdown,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            self._set_cached_data(cache_key, result)
            logger.info(f"Criticality distribution calculated and cached for user {user_id}, timeframe {timeframe}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating criticality distribution for user {user_id}: {e}", exc_info=True)
            return {
                "timeframe": timeframe,
                "distribution": {
                    "severe": {"count": 0, "percentage": 0.0},
                    "high": {"count": 0, "percentage": 0.0},
                    "medium": {"count": 0, "percentage": 0.0},
                    "low": {"count": 0, "percentage": 0.0}
                },
                "total_issues": 0,
                "severity_breakdown": {},
                "generated_at": datetime.utcnow().isoformat()
            }
    
    def _get_severity_aliases(self, severity: str) -> List[str]:
        """Get list of severity aliases for categorization."""
        aliases = {
            "severe": ["critical", "severe"],
            "high": ["high"],
            "medium": ["medium", "moderate"],
            "low": ["low", "minor", "info"]
        }
        return aliases.get(severity, [severity])
