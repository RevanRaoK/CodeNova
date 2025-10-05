"""
Enhanced Feedback Service for AI suggestions with detailed rejection reasons.

This service handles:
- Creating feedback records for AI suggestions (accept/reject)
- Retrieving feedback analytics and aggregation
- Managing rejection reasons and custom feedback
- Background tasks for AI learning pattern updates

Requirements covered: 1.1, 1.2, 1.3, 1.4, 1.5
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from collections import defaultdict, Counter
import uuid

from app.models.enhanced_feedback import EnhancedFeedback, FeedbackAction
from app.models.users import User


class EnhancedFeedbackService:
    """Service class for managing enhanced feedback on AI suggestions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_feedback(
        self, 
        suggestion_id: str, 
        user_id: int, 
        action: FeedbackAction,
        rejection_reasons: Optional[List[str]] = None,
        custom_reason: Optional[str] = None,
        suggestion_type: Optional[str] = None,
        confidence_score: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> EnhancedFeedback:
        """
        Create a new feedback record for an AI suggestion.
        
        Args:
            suggestion_id: Unique identifier for the AI suggestion
            user_id: ID of the user providing feedback
            action: Accept or reject action
            rejection_reasons: List of predefined rejection reasons (required if action is REJECT)
            custom_reason: Custom reason text (optional)
            suggestion_type: Type of AI suggestion
            confidence_score: AI confidence level
            context_data: Additional context about the suggestion
            
        Returns:
            EnhancedFeedback: The created feedback record
            
        Requirements: 1.1, 1.2, 1.3, 1.4
        """
        # Validate rejection reasons for reject actions
        if action == FeedbackAction.REJECT and not rejection_reasons:
            raise ValueError("Rejection reasons are required when rejecting a suggestion")
        
        # Check if user already provided feedback for this suggestion
        existing_feedback = self.db.query(EnhancedFeedback).filter(
            and_(
                EnhancedFeedback.suggestion_id == suggestion_id,
                EnhancedFeedback.user_id == user_id
            )
        ).first()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.action = action
            existing_feedback.rejection_reasons = rejection_reasons
            existing_feedback.custom_reason = custom_reason
            existing_feedback.suggestion_type = suggestion_type
            existing_feedback.confidence_score = confidence_score
            existing_feedback.context_data = context_data or {}
            existing_feedback.timestamp = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_feedback)
            return existing_feedback
        
        # Create new feedback record
        feedback = EnhancedFeedback(
            id=str(uuid.uuid4()),
            suggestion_id=suggestion_id,
            user_id=user_id,
            action=action,
            rejection_reasons=rejection_reasons,
            custom_reason=custom_reason,
            suggestion_type=suggestion_type,
            confidence_score=confidence_score,
            context_data=context_data or {},
            timestamp=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        
        return feedback
    
    def get_feedback_by_id(self, feedback_id: str) -> Optional[EnhancedFeedback]:
        """Get a specific feedback record by ID."""
        return self.db.query(EnhancedFeedback).filter(EnhancedFeedback.id == feedback_id).first()
    
    def get_feedback_by_suggestion(self, suggestion_id: str) -> List[EnhancedFeedback]:
        """Get all feedback records for a specific suggestion."""
        return self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.suggestion_id == suggestion_id
        ).order_by(desc(EnhancedFeedback.timestamp)).all()
    
    def get_user_feedback_history(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[EnhancedFeedback], int]:
        """
        Get paginated feedback history for a user.
        
        Returns:
            Tuple of (feedback_records, total_count)
        """
        query = self.db.query(EnhancedFeedback).filter(EnhancedFeedback.user_id == user_id)
        total_count = query.count()
        
        feedback_records = query.order_by(desc(EnhancedFeedback.timestamp)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return feedback_records, total_count
    
    def get_feedback_analytics(
        self, 
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        suggestion_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive feedback analytics.
        
        Args:
            user_id: Optional filter by user ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            suggestion_type: Optional filter by suggestion type
            
        Returns:
            Dict containing analytics data
            
        Requirements: 1.4, 1.5
        """
        # Build base query
        query = self.db.query(EnhancedFeedback)
        
        # Apply filters
        if user_id:
            query = query.filter(EnhancedFeedback.user_id == user_id)
        
        if start_date:
            query = query.filter(EnhancedFeedback.timestamp >= start_date)
        
        if end_date:
            query = query.filter(EnhancedFeedback.timestamp <= end_date)
        
        if suggestion_type:
            query = query.filter(EnhancedFeedback.suggestion_type == suggestion_type)
        
        # Get all feedback records for analysis
        feedback_records = query.all()
        total_count = len(feedback_records)
        
        if total_count == 0:
            return self._empty_analytics_response()
        
        # Calculate acceptance and rejection rates
        accept_count = sum(1 for f in feedback_records if f.action == FeedbackAction.ACCEPT)
        reject_count = sum(1 for f in feedback_records if f.action == FeedbackAction.REJECT)
        
        acceptance_rate = (accept_count / total_count) * 100
        rejection_rate = (reject_count / total_count) * 100
        
        # Analyze rejection reasons
        rejection_reasons_analysis = self._analyze_rejection_reasons(feedback_records)
        
        # Feedback by date
        feedback_by_date = self._calculate_feedback_by_date(feedback_records)
        
        # Feedback by suggestion type
        feedback_by_type = self._calculate_feedback_by_suggestion_type(feedback_records)
        
        # Learning progress indicators
        learning_progress = self._calculate_learning_progress(feedback_records)
        
        return {
            'total_feedback_count': total_count,
            'acceptance_rate': round(acceptance_rate, 2),
            'rejection_rate': round(rejection_rate, 2),
            'accept_count': accept_count,
            'reject_count': reject_count,
            'rejection_reasons_analysis': rejection_reasons_analysis,
            'feedback_by_date': feedback_by_date,
            'feedback_by_suggestion_type': feedback_by_type,
            'learning_progress': learning_progress,
            'period_start': start_date.isoformat() if start_date else None,
            'period_end': end_date.isoformat() if end_date else None
        }
    
    def _empty_analytics_response(self) -> Dict[str, Any]:
        """Return empty analytics response when no data is available."""
        return {
            'total_feedback_count': 0,
            'acceptance_rate': 0.0,
            'rejection_rate': 0.0,
            'accept_count': 0,
            'reject_count': 0,
            'rejection_reasons_analysis': {},
            'feedback_by_date': {},
            'feedback_by_suggestion_type': {},
            'learning_progress': {},
            'period_start': None,
            'period_end': None
        }
    
    def _analyze_rejection_reasons(self, feedback_records: List[EnhancedFeedback]) -> Dict[str, Any]:
        """Analyze rejection reasons from feedback records."""
        rejection_records = [f for f in feedback_records if f.action == FeedbackAction.REJECT]
        
        if not rejection_records:
            return {'common_reasons': {}, 'custom_reasons': [], 'total_rejections': 0}
        
        # Count predefined rejection reasons
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
        
        # Sort reasons by frequency
        sorted_reasons = dict(sorted(reason_counts.items(), key=lambda x: x[1], reverse=True))
        
        return {
            'common_reasons': sorted_reasons,
            'custom_reasons': custom_reasons[-10:],  # Last 10 custom reasons
            'total_rejections': len(rejection_records),
            'reasons_distribution': {
                reason: round((count / len(rejection_records)) * 100, 2)
                for reason, count in sorted_reasons.items()
            }
        }
    
    def _calculate_feedback_by_date(self, feedback_records: List[EnhancedFeedback]) -> Dict[str, Dict[str, int]]:
        """Calculate feedback count by date and action."""
        feedback_by_date = defaultdict(lambda: {'accept': 0, 'reject': 0})
        
        for record in feedback_records:
            date_str = record.timestamp.strftime('%Y-%m-%d')
            action_str = record.action.value
            feedback_by_date[date_str][action_str] += 1
        
        return dict(feedback_by_date)
    
    def _calculate_feedback_by_suggestion_type(self, feedback_records: List[EnhancedFeedback]) -> Dict[str, Dict[str, int]]:
        """Calculate feedback count by suggestion type."""
        feedback_by_type = defaultdict(lambda: {'accept': 0, 'reject': 0})
        
        for record in feedback_records:
            suggestion_type = record.suggestion_type or 'unknown'
            action_str = record.action.value
            feedback_by_type[suggestion_type][action_str] += 1
        
        return dict(feedback_by_type)
    
    def _calculate_learning_progress(self, feedback_records: List[EnhancedFeedback]) -> Dict[str, Any]:
        """Calculate learning progress indicators."""
        if len(feedback_records) < 10:  # Need minimum data for meaningful progress
            return {'insufficient_data': True}
        
        # Sort by timestamp
        sorted_records = sorted(feedback_records, key=lambda x: x.timestamp)
        
        # Calculate acceptance rate over time (weekly windows)
        weekly_acceptance = []
        current_week_start = sorted_records[0].timestamp
        week_records = []
        
        for record in sorted_records:
            # If record is more than 7 days from current week start, process current week
            if (record.timestamp - current_week_start).days >= 7:
                if week_records:
                    week_accepts = sum(1 for r in week_records if r.action == FeedbackAction.ACCEPT)
                    acceptance_rate = (week_accepts / len(week_records)) * 100
                    weekly_acceptance.append({
                        'week_start': current_week_start.strftime('%Y-%m-%d'),
                        'acceptance_rate': round(acceptance_rate, 2),
                        'total_feedback': len(week_records)
                    })
                
                # Start new week
                current_week_start = record.timestamp
                week_records = [record]
            else:
                week_records.append(record)
        
        # Process final week
        if week_records:
            week_accepts = sum(1 for r in week_records if r.action == FeedbackAction.ACCEPT)
            acceptance_rate = (week_accepts / len(week_records)) * 100
            weekly_acceptance.append({
                'week_start': current_week_start.strftime('%Y-%m-%d'),
                'acceptance_rate': round(acceptance_rate, 2),
                'total_feedback': len(week_records)
            })
        
        # Calculate trend
        if len(weekly_acceptance) >= 2:
            recent_rate = weekly_acceptance[-1]['acceptance_rate']
            previous_rate = weekly_acceptance[-2]['acceptance_rate']
            trend = 'improving' if recent_rate > previous_rate else 'declining' if recent_rate < previous_rate else 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'weekly_acceptance_rates': weekly_acceptance,
            'trend': trend,
            'total_weeks': len(weekly_acceptance),
            'latest_acceptance_rate': weekly_acceptance[-1]['acceptance_rate'] if weekly_acceptance else 0
        }
    
    def update_ai_learning_patterns(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update AI learning patterns based on feedback data.
        This is a background task that processes feedback for model improvement.
        
        Args:
            feedback_data: Aggregated feedback data for learning
            
        Returns:
            Dict containing update results and metrics
            
        Requirements: 1.5
        """
        # Get recent feedback for learning (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_feedback = self.db.query(EnhancedFeedback).filter(
            EnhancedFeedback.timestamp >= thirty_days_ago
        ).all()
        
        if not recent_feedback:
            return {'status': 'no_recent_feedback', 'processed_count': 0}
        
        # Analyze patterns in rejected suggestions
        rejection_patterns = self._extract_rejection_patterns(recent_feedback)
        
        # Analyze patterns in accepted suggestions
        acceptance_patterns = self._extract_acceptance_patterns(recent_feedback)
        
        # Calculate confidence score adjustments
        confidence_adjustments = self._calculate_confidence_adjustments(recent_feedback)
        
        # Prepare learning data for AI model
        learning_data = {
            'rejection_patterns': rejection_patterns,
            'acceptance_patterns': acceptance_patterns,
            'confidence_adjustments': confidence_adjustments,
            'feedback_count': len(recent_feedback),
            'processed_at': datetime.utcnow().isoformat(),
            'period_days': 30
        }
        
        # In a real implementation, this would trigger model retraining
        # For now, we'll store the learning data for future processing
        
        return {
            'status': 'success',
            'processed_count': len(recent_feedback),
            'learning_data': learning_data,
            'patterns_identified': len(rejection_patterns) + len(acceptance_patterns)
        }
    
    def _extract_rejection_patterns(self, feedback_records: List[EnhancedFeedback]) -> List[Dict[str, Any]]:
        """Extract patterns from rejected suggestions for learning."""
        rejection_records = [f for f in feedback_records if f.action == FeedbackAction.REJECT]
        
        patterns = []
        for record in rejection_records:
            if record.rejection_reasons:
                pattern = {
                    'suggestion_id': record.suggestion_id,
                    'suggestion_type': record.suggestion_type,
                    'rejection_reasons': record.rejection_reasons,
                    'custom_reason': record.custom_reason,
                    'confidence_score': record.confidence_score,
                    'context_data': record.context_data,
                    'timestamp': record.timestamp.isoformat()
                }
                patterns.append(pattern)
        
        return patterns
    
    def _extract_acceptance_patterns(self, feedback_records: List[EnhancedFeedback]) -> List[Dict[str, Any]]:
        """Extract patterns from accepted suggestions for learning."""
        acceptance_records = [f for f in feedback_records if f.action == FeedbackAction.ACCEPT]
        
        patterns = []
        for record in acceptance_records:
            pattern = {
                'suggestion_id': record.suggestion_id,
                'suggestion_type': record.suggestion_type,
                'confidence_score': record.confidence_score,
                'context_data': record.context_data,
                'timestamp': record.timestamp.isoformat()
            }
            patterns.append(pattern)
        
        return patterns
    
    def _calculate_confidence_adjustments(self, feedback_records: List[EnhancedFeedback]) -> Dict[str, Any]:
        """Calculate confidence score adjustments based on feedback."""
        confidence_feedback = defaultdict(list)
        
        for record in feedback_records:
            if record.confidence_score:
                confidence_feedback[record.confidence_score].append(record.action.value)
        
        adjustments = {}
        for confidence_level, actions in confidence_feedback.items():
            accept_count = sum(1 for action in actions if action == 'accept')
            total_count = len(actions)
            actual_accuracy = (accept_count / total_count) * 100 if total_count > 0 else 0
            
            adjustments[confidence_level] = {
                'actual_accuracy': round(actual_accuracy, 2),
                'feedback_count': total_count,
                'suggested_adjustment': self._suggest_confidence_adjustment(confidence_level, actual_accuracy)
            }
        
        return adjustments
    
    def _suggest_confidence_adjustment(self, confidence_level: str, actual_accuracy: float) -> str:
        """Suggest confidence level adjustments based on actual accuracy."""
        # Simple heuristic for confidence adjustment
        if confidence_level == 'high' and actual_accuracy < 80:
            return 'lower_confidence'
        elif confidence_level == 'low' and actual_accuracy > 90:
            return 'raise_confidence'
        elif confidence_level == 'medium' and actual_accuracy < 60:
            return 'lower_confidence'
        elif confidence_level == 'medium' and actual_accuracy > 95:
            return 'raise_confidence'
        else:
            return 'maintain_confidence'