"""
Feedback Repository for database operations.

This repository handles:
- CRUD operations for enhanced feedback records
- Complex queries for analytics and reporting
- Data aggregation for feedback statistics

Requirements covered: 1.1, 1.2, 1.3, 1.4, 1.5
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, text
from collections import defaultdict

from app.models.enhanced_feedback import EnhancedFeedback, FeedbackAction
from app.models.users import User


class FeedbackRepository:
    """Repository class for feedback database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_feedback(self, feedback: EnhancedFeedback) -> EnhancedFeedback:
        """
        Create a new feedback record in the database.
        
        Args:
            feedback: EnhancedFeedback instance to create
            
        Returns:
            EnhancedFeedback: The created feedback record
        """
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
    
    def get_feedback_by_id(self, feedback_id: str) -> Optional[EnhancedFeedback]:
        """
        Get a feedback record by its ID.
        
        Args:
            feedback_id: Unique identifier for the feedback record
            
        Returns:
            Optional[EnhancedFeedback]: The feedback record if found, None otherwise
        """
        return self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.id == feedback_id
        ).first()
    
    def get_feedback_by_suggestion_id(self, suggestion_id: str) -> List[EnhancedFeedback]:
        """
        Get all feedback records for a specific suggestion.
        
        Args:
            suggestion_id: Unique identifier for the AI suggestion
            
        Returns:
            List[EnhancedFeedback]: List of feedback records for the suggestion
        """
        return self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.suggestion_id == suggestion_id
        ).order_by(desc(EnhancedFeedback.timestamp)).all()
    
    def get_feedback_by_user_and_suggestion(
        self, 
        user_id: int, 
        suggestion_id: str
    ) -> Optional[EnhancedFeedback]:
        """
        Get feedback record for a specific user and suggestion combination.
        
        Args:
            user_id: ID of the user
            suggestion_id: ID of the suggestion
            
        Returns:
            Optional[EnhancedFeedback]: The feedback record if found, None otherwise
        """
        return self.db.query(EnhancedFeedback).filter(
            and_(
                EnhancedFeedback.user_id == user_id,
                EnhancedFeedback.suggestion_id == suggestion_id
            )
        ).first()
    
    def get_user_feedback_paginated(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20,
        action_filter: Optional[FeedbackAction] = None,
        suggestion_type_filter: Optional[str] = None
    ) -> Tuple[List[EnhancedFeedback], int]:
        """
        Get paginated feedback records for a user with optional filters.
        
        Args:
            user_id: ID of the user
            page: Page number (1-based)
            page_size: Number of records per page
            action_filter: Optional filter by feedback action
            suggestion_type_filter: Optional filter by suggestion type
            
        Returns:
            Tuple[List[EnhancedFeedback], int]: (feedback_records, total_count)
        """
        query = self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.user_id == user_id
        )
        
        # Apply filters
        if action_filter:
            query = query.filter(EnhancedFeedback.action == action_filter)
        
        if suggestion_type_filter:
            query = query.filter(EnhancedFeedback.suggestion_type == suggestion_type_filter)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated results
        feedback_records = query.order_by(desc(EnhancedFeedback.timestamp)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return feedback_records, total_count
    
    def get_feedback_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        user_id: Optional[int] = None,
        suggestion_type: Optional[str] = None
    ) -> List[EnhancedFeedback]:
        """
        Get feedback records within a date range with optional filters.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            user_id: Optional filter by user ID
            suggestion_type: Optional filter by suggestion type
            
        Returns:
            List[EnhancedFeedback]: List of feedback records in the date range
        """
        query = self.db.query(EnhancedFeedback).filter(
            and_(
                EnhancedFeedback.timestamp >= start_date,
                EnhancedFeedback.timestamp <= end_date
            )
        )
        
        if user_id:
            query = query.filter(EnhancedFeedback.user_id == user_id)
        
        if suggestion_type:
            query = query.filter(EnhancedFeedback.suggestion_type == suggestion_type)
        
        return query.order_by(desc(EnhancedFeedback.timestamp)).all()
    
    def get_feedback_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        suggestion_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated feedback statistics.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            user_id: Optional user ID filter
            suggestion_type: Optional suggestion type filter
            
        Returns:
            Dict[str, Any]: Aggregated statistics
        """
        query = self.db.query(EnhancedFeedback)
        
        # Apply filters
        if start_date:
            query = query.filter(EnhancedFeedback.timestamp >= start_date)
        
        if end_date:
            query = query.filter(EnhancedFeedback.timestamp <= end_date)
        
        if user_id:
            query = query.filter(EnhancedFeedback.user_id == user_id)
        
        if suggestion_type:
            query = query.filter(EnhancedFeedback.suggestion_type == suggestion_type)
        
        # Get basic counts
        total_count = query.count()
        accept_count = query.filter(EnhancedFeedback.action == FeedbackAction.ACCEPT).count()
        reject_count = query.filter(EnhancedFeedback.action == FeedbackAction.REJECT).count()
        
        # Calculate rates
        acceptance_rate = (accept_count / total_count * 100) if total_count > 0 else 0
        rejection_rate = (reject_count / total_count * 100) if total_count > 0 else 0
        
        return {
            'total_count': total_count,
            'accept_count': accept_count,
            'reject_count': reject_count,
            'acceptance_rate': round(acceptance_rate, 2),
            'rejection_rate': round(rejection_rate, 2)
        }
    
    def get_daily_feedback_counts(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None
    ) -> Dict[str, Dict[str, int]]:
        """
        Get daily feedback counts within a date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            user_id: Optional user ID filter
            
        Returns:
            Dict[str, Dict[str, int]]: Daily counts by action type
        """
        query = self.db.query(
            func.date(EnhancedFeedback.timestamp).label('date'),
            EnhancedFeedback.action,
            func.count(EnhancedFeedback.id).label('count')
        ).filter(
            and_(
                EnhancedFeedback.timestamp >= start_date,
                EnhancedFeedback.timestamp <= end_date
            )
        )
        
        if user_id:
            query = query.filter(EnhancedFeedback.user_id == user_id)
        
        results = query.group_by(
            func.date(EnhancedFeedback.timestamp),
            EnhancedFeedback.action
        ).all()
        
        # Organize results by date
        daily_counts = defaultdict(lambda: {'accept': 0, 'reject': 0})
        
        for result in results:
            date_str = result.date.strftime('%Y-%m-%d')
            action_str = result.action.value
            daily_counts[date_str][action_str] = result.count
        
        return dict(daily_counts)
    
    def get_rejection_reasons_analysis(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze rejection reasons from feedback records.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            user_id: Optional user ID filter
            
        Returns:
            Dict[str, Any]: Analysis of rejection reasons
        """
        query = self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.action == FeedbackAction.REJECT
        )
        
        if start_date:
            query = query.filter(EnhancedFeedback.timestamp >= start_date)
        
        if end_date:
            query = query.filter(EnhancedFeedback.timestamp <= end_date)
        
        if user_id:
            query = query.filter(EnhancedFeedback.user_id == user_id)
        
        rejection_records = query.all()
        
        # Count predefined reasons
        reason_counts = defaultdict(int)
        custom_reasons = []
        
        for record in rejection_records:
            if record.rejection_reasons:
                for reason in record.rejection_reasons:
                    reason_counts[reason] += 1
            
            if record.custom_reason:
                custom_reasons.append({
                    'reason': record.custom_reason,
                    'timestamp': record.timestamp.isoformat(),
                    'suggestion_type': record.suggestion_type
                })
        
        # Sort by frequency
        sorted_reasons = dict(sorted(reason_counts.items(), key=lambda x: x[1], reverse=True))
        
        return {
            'common_reasons': sorted_reasons,
            'custom_reasons': custom_reasons[-20:],  # Last 20 custom reasons
            'total_rejections': len(rejection_records),
            'unique_reasons_count': len(reason_counts)
        }
    
    def get_suggestion_type_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics grouped by suggestion type.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            user_id: Optional user ID filter
            
        Returns:
            Dict[str, Dict[str, Any]]: Statistics by suggestion type
        """
        query = self.db.query(
            EnhancedFeedback.suggestion_type,
            EnhancedFeedback.action,
            func.count(EnhancedFeedback.id).label('count')
        )
        
        if start_date:
            query = query.filter(EnhancedFeedback.timestamp >= start_date)
        
        if end_date:
            query = query.filter(EnhancedFeedback.timestamp <= end_date)
        
        if user_id:
            query = query.filter(EnhancedFeedback.user_id == user_id)
        
        results = query.group_by(
            EnhancedFeedback.suggestion_type,
            EnhancedFeedback.action
        ).all()
        
        # Organize results by suggestion type
        type_stats = defaultdict(lambda: {'accept': 0, 'reject': 0, 'total': 0})
        
        for result in results:
            suggestion_type = result.suggestion_type or 'unknown'
            action_str = result.action.value
            count = result.count
            
            type_stats[suggestion_type][action_str] = count
            type_stats[suggestion_type]['total'] += count
        
        # Calculate rates for each type
        for suggestion_type, stats in type_stats.items():
            total = stats['total']
            if total > 0:
                stats['acceptance_rate'] = round((stats['accept'] / total) * 100, 2)
                stats['rejection_rate'] = round((stats['reject'] / total) * 100, 2)
            else:
                stats['acceptance_rate'] = 0.0
                stats['rejection_rate'] = 0.0
        
        return dict(type_stats)
    
    def get_recent_feedback_for_learning(
        self, 
        days: int = 30,
        limit: Optional[int] = None
    ) -> List[EnhancedFeedback]:
        """
        Get recent feedback records for AI learning purposes.
        
        Args:
            days: Number of days to look back
            limit: Optional limit on number of records
            
        Returns:
            List[EnhancedFeedback]: Recent feedback records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.timestamp >= cutoff_date
        ).order_by(desc(EnhancedFeedback.timestamp))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def update_feedback(self, feedback: EnhancedFeedback) -> EnhancedFeedback:
        """
        Update an existing feedback record.
        
        Args:
            feedback: EnhancedFeedback instance with updated data
            
        Returns:
            EnhancedFeedback: The updated feedback record
        """
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
    
    def delete_feedback(self, feedback_id: str) -> bool:
        """
        Delete a feedback record by ID.
        
        Args:
            feedback_id: ID of the feedback record to delete
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        feedback = self.get_feedback_by_id(feedback_id)
        if feedback:
            self.db.delete(feedback)
            self.db.commit()
            return True
        return False
    
    def get_user_feedback_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get a summary of feedback activity for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict[str, Any]: Summary statistics for the user
        """
        # Get all feedback for the user
        user_feedback = self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.user_id == user_id
        ).all()
        
        if not user_feedback:
            return {
                'total_feedback': 0,
                'acceptance_rate': 0.0,
                'rejection_rate': 0.0,
                'most_recent_feedback': None,
                'feedback_streak_days': 0
            }
        
        # Calculate basic stats
        total_count = len(user_feedback)
        accept_count = sum(1 for f in user_feedback if f.action == FeedbackAction.ACCEPT)
        reject_count = sum(1 for f in user_feedback if f.action == FeedbackAction.REJECT)
        
        acceptance_rate = (accept_count / total_count) * 100
        rejection_rate = (reject_count / total_count) * 100
        
        # Get most recent feedback
        most_recent = max(user_feedback, key=lambda f: f.timestamp)
        
        # Calculate feedback streak (consecutive days with feedback)
        feedback_dates = sorted(set(f.timestamp.date() for f in user_feedback), reverse=True)
        streak_days = 0
        
        if feedback_dates:
            current_date = datetime.utcnow().date()
            for i, feedback_date in enumerate(feedback_dates):
                expected_date = current_date - timedelta(days=i)
                if feedback_date == expected_date:
                    streak_days += 1
                else:
                    break
        
        return {
            'total_feedback': total_count,
            'acceptance_rate': round(acceptance_rate, 2),
            'rejection_rate': round(rejection_rate, 2),
            'accept_count': accept_count,
            'reject_count': reject_count,
            'most_recent_feedback': most_recent.timestamp.isoformat(),
            'feedback_streak_days': streak_days,
            'first_feedback': min(user_feedback, key=lambda f: f.timestamp).timestamp.isoformat()
        }