"""
Feedback collection service for AST-based code analysis and learning pipeline.

This service handles:
- Recording and validating user feedback on AI suggestions
- Aggregating feedback statistics for model improvement
- Preparing training data for model fine-tuning

Requirements covered: 2.1, 2.2, 2.3, 2.4
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from collections import defaultdict, Counter

from app.models.feedback import FeedbackRecord, Issue, ModelVersion
from app.models.users import User
from app.schemas.feedback import (
    FeedbackSubmissionRequest, FeedbackResponse, FeedbackStatsResponse,
    FeedbackType, DateRange, FeedbackValidationRequest
)


class FeedbackValidationError(Exception):
    """Custom exception for feedback validation errors."""
    pass


class FeedbackService:
    """Service class for managing user feedback on AI code suggestions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_feedback(
        self, 
        user_id: int, 
        feedback_request: FeedbackSubmissionRequest
    ) -> FeedbackRecord:
        """
        Record user feedback for a specific issue.
        
        Args:
            user_id: ID of the user providing feedback
            feedback_request: Feedback submission data
            
        Returns:
            FeedbackRecord: The created feedback record
            
        Raises:
            FeedbackValidationError: If validation fails
            
        Requirements: 2.1, 2.2, 2.3
        """
        # Validate that the issue exists
        issue = self.db.query(Issue).filter(Issue.id == feedback_request.issue_id).first()
        if not issue:
            raise FeedbackValidationError(f"Issue with ID {feedback_request.issue_id} not found")
        
        # Check if user already provided feedback for this issue
        existing_feedback = self.db.query(FeedbackRecord).filter(
            and_(
                FeedbackRecord.issue_id == feedback_request.issue_id,
                FeedbackRecord.user_id == user_id
            )
        ).first()
        
        if existing_feedback:
            # Update existing feedback instead of creating duplicate
            return self._update_existing_feedback(existing_feedback, feedback_request)
        
        # Convert feedback type to numeric value
        feedback_value = self._get_feedback_value(feedback_request.feedback_type)
        
        # Create new feedback record
        feedback_record = FeedbackRecord(
            issue_id=feedback_request.issue_id,
            user_id=user_id,
            feedback_type=feedback_request.feedback_type.value,
            feedback_value=feedback_value,
            feedback_comment=feedback_request.feedback_comment,
            modified_suggestion=feedback_request.modified_suggestion,
            user_experience_level=feedback_request.user_experience_level.value if feedback_request.user_experience_level else None,
            code_review_context=feedback_request.code_review_context.value if feedback_request.code_review_context else None,
            context_data=feedback_request.context_data or {},
            is_validated=False,
            validation_score=None
        )
        
        self.db.add(feedback_record)
        self.db.commit()
        self.db.refresh(feedback_record)
        
        return feedback_record
    
    def _update_existing_feedback(
        self, 
        existing_feedback: FeedbackRecord, 
        feedback_request: FeedbackSubmissionRequest
    ) -> FeedbackRecord:
        """Update existing feedback record with new data."""
        existing_feedback.feedback_type = feedback_request.feedback_type.value
        existing_feedback.feedback_value = self._get_feedback_value(feedback_request.feedback_type)
        existing_feedback.feedback_comment = feedback_request.feedback_comment
        existing_feedback.modified_suggestion = feedback_request.modified_suggestion
        existing_feedback.user_experience_level = feedback_request.user_experience_level.value if feedback_request.user_experience_level else None
        existing_feedback.code_review_context = feedback_request.code_review_context.value if feedback_request.code_review_context else None
        existing_feedback.context_data = feedback_request.context_data or {}
        existing_feedback.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(existing_feedback)
        
        return existing_feedback
    
    def _get_feedback_value(self, feedback_type: FeedbackType) -> int:
        """Convert feedback type to numeric value for analysis."""
        feedback_values = {
            FeedbackType.ACCEPT: 1,
            FeedbackType.REJECT: -1,
            FeedbackType.MODIFY: 0,  # Neutral - user engaged but changed suggestion
            FeedbackType.IGNORE: 0   # Neutral - no strong opinion
        }
        return feedback_values[feedback_type]
    
    def get_feedback_by_id(self, feedback_id: int) -> Optional[FeedbackRecord]:
        """Get a specific feedback record by ID."""
        return self.db.query(FeedbackRecord).filter(FeedbackRecord.id == feedback_id).first()
    
    def get_feedback_for_issue(self, issue_id: str) -> List[FeedbackRecord]:
        """Get all feedback records for a specific issue."""
        return self.db.query(FeedbackRecord).filter(
            FeedbackRecord.issue_id == issue_id
        ).order_by(desc(FeedbackRecord.created_at)).all()
    
    def get_user_feedback_history(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[FeedbackRecord], int]:
        """
        Get paginated feedback history for a user.
        
        Returns:
            Tuple of (feedback_records, total_count)
        """
        query = self.db.query(FeedbackRecord).filter(FeedbackRecord.user_id == user_id)
        total_count = query.count()
        
        feedback_records = query.order_by(desc(FeedbackRecord.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return feedback_records, total_count
    
    def get_feedback_statistics(
        self, 
        date_range: Optional[DateRange] = None,
        pattern_type: Optional[str] = None,
        user_experience_level: Optional[str] = None
    ) -> FeedbackStatsResponse:
        """
        Generate comprehensive feedback statistics.
        
        Args:
            date_range: Optional date range filter
            pattern_type: Optional filter by issue pattern type
            user_experience_level: Optional filter by user experience
            
        Returns:
            FeedbackStatsResponse: Aggregated statistics
            
        Requirements: 2.4, 4.1, 4.2
        """
        # Build base query
        query = self.db.query(FeedbackRecord).join(Issue)
        
        # Apply filters
        if date_range:
            query = query.filter(
                and_(
                    FeedbackRecord.created_at >= date_range.start_date,
                    FeedbackRecord.created_at <= date_range.end_date
                )
            )
        
        if pattern_type:
            query = query.filter(Issue.pattern_type == pattern_type)
        
        if user_experience_level:
            query = query.filter(FeedbackRecord.user_experience_level == user_experience_level)
        
        # Get all feedback records for analysis
        feedback_records = query.all()
        total_count = len(feedback_records)
        
        if total_count == 0:
            return self._empty_stats_response()
        
        # Calculate basic rates
        feedback_counts = Counter(record.feedback_type for record in feedback_records)
        acceptance_rate = (feedback_counts.get('accept', 0) / total_count) * 100
        rejection_rate = (feedback_counts.get('reject', 0) / total_count) * 100
        modification_rate = (feedback_counts.get('modify', 0) / total_count) * 100
        
        # Feedback by date
        feedback_by_date = self._calculate_feedback_by_date(feedback_records)
        
        # Feedback by experience level
        feedback_by_experience = self._calculate_feedback_by_experience(feedback_records)
        
        # Pattern-specific statistics
        pattern_feedback_stats = self._calculate_pattern_feedback_stats(feedback_records)
        
        # Response time analysis
        average_response_time = self._calculate_average_response_time(feedback_records)
        
        # Most common patterns
        most_common_patterns = self._get_most_common_patterns(feedback_records)
        
        return FeedbackStatsResponse(
            total_feedback_count=total_count,
            acceptance_rate=round(acceptance_rate, 2),
            rejection_rate=round(rejection_rate, 2),
            modification_rate=round(modification_rate, 2),
            feedback_breakdown=dict(feedback_counts),
            feedback_by_date=feedback_by_date,
            feedback_by_experience=feedback_by_experience,
            pattern_feedback_stats=pattern_feedback_stats,
            average_response_time_hours=average_response_time,
            most_common_patterns=most_common_patterns
        )
    
    def _empty_stats_response(self) -> FeedbackStatsResponse:
        """Return empty statistics response when no data is available."""
        return FeedbackStatsResponse(
            total_feedback_count=0,
            acceptance_rate=0.0,
            rejection_rate=0.0,
            modification_rate=0.0,
            feedback_breakdown={},
            feedback_by_date={},
            feedback_by_experience={},
            pattern_feedback_stats={},
            average_response_time_hours=None,
            most_common_patterns=[]
        )
    
    def _calculate_feedback_by_date(self, feedback_records: List[FeedbackRecord]) -> Dict[str, int]:
        """Calculate feedback count by date."""
        feedback_by_date = defaultdict(int)
        for record in feedback_records:
            date_str = record.created_at.strftime('%Y-%m-%d')
            feedback_by_date[date_str] += 1
        return dict(feedback_by_date)
    
    def _calculate_feedback_by_experience(self, feedback_records: List[FeedbackRecord]) -> Dict[str, int]:
        """Calculate feedback count by user experience level."""
        feedback_by_experience = defaultdict(int)
        for record in feedback_records:
            level = record.user_experience_level or 'unknown'
            feedback_by_experience[level] += 1
        return dict(feedback_by_experience)
    
    def _calculate_pattern_feedback_stats(self, feedback_records: List[FeedbackRecord]) -> Dict[str, Dict[str, float]]:
        """Calculate feedback statistics by pattern type."""
        pattern_stats = defaultdict(lambda: defaultdict(int))
        
        # Group feedback by pattern type
        for record in feedback_records:
            pattern_type = record.issue.pattern_type
            pattern_stats[pattern_type][record.feedback_type] += 1
        
        # Calculate rates for each pattern
        result = {}
        for pattern_type, feedback_counts in pattern_stats.items():
            total = sum(feedback_counts.values())
            if total > 0:
                result[pattern_type] = {
                    'acceptance_rate': round((feedback_counts.get('accept', 0) / total) * 100, 2),
                    'rejection_rate': round((feedback_counts.get('reject', 0) / total) * 100, 2),
                    'modification_rate': round((feedback_counts.get('modify', 0) / total) * 100, 2),
                    'total_feedback': total
                }
        
        return result
    
    def _calculate_average_response_time(self, feedback_records: List[FeedbackRecord]) -> Optional[float]:
        """Calculate average time between issue creation and feedback submission."""
        response_times = []
        
        for record in feedback_records:
            if record.issue and record.issue.created_at:
                time_diff = record.created_at - record.issue.created_at
                response_times.append(time_diff.total_seconds() / 3600)  # Convert to hours
        
        if response_times:
            return round(sum(response_times) / len(response_times), 2)
        return None
    
    def _get_most_common_patterns(self, feedback_records: List[FeedbackRecord], limit: int = 10) -> List[str]:
        """Get the most frequently occurring issue patterns."""
        pattern_counts = Counter(record.issue.pattern_type for record in feedback_records if record.issue)
        return [pattern for pattern, _ in pattern_counts.most_common(limit)]
    
    def validate_feedback(
        self, 
        feedback_id: int, 
        validation_request: FeedbackValidationRequest
    ) -> FeedbackRecord:
        """
        Validate feedback quality (admin function).
        
        Args:
            feedback_id: ID of the feedback record to validate
            validation_request: Validation data
            
        Returns:
            FeedbackRecord: Updated feedback record
            
        Raises:
            FeedbackValidationError: If feedback not found
        """
        feedback_record = self.get_feedback_by_id(feedback_id)
        if not feedback_record:
            raise FeedbackValidationError(f"Feedback record with ID {feedback_id} not found")
        
        feedback_record.is_validated = validation_request.is_valid
        feedback_record.validation_score = validation_request.validation_score
        feedback_record.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(feedback_record)
        
        return feedback_record
    
    def prepare_training_data(
        self, 
        feedback_threshold: int = 10,
        min_validation_score: float = 0.7
    ) -> Dict[str, Any]:
        """
        Prepare training data from validated feedback for model fine-tuning.
        
        Args:
            feedback_threshold: Minimum number of feedback records per pattern
            min_validation_score: Minimum validation score for inclusion
            
        Returns:
            Dict containing training data and metadata
            
        Requirements: 3.1, 3.2, 3.3
        """
        # Query validated feedback with sufficient quality
        validated_feedback = self.db.query(FeedbackRecord).filter(
            and_(
                FeedbackRecord.is_validated == True,
                or_(
                    FeedbackRecord.validation_score >= min_validation_score,
                    FeedbackRecord.validation_score.is_(None)  # Include unscored but validated feedback
                )
            )
        ).join(Issue).all()
        
        # Group by pattern type and prepare training examples
        training_data = defaultdict(list)
        
        for feedback in validated_feedback:
            issue = feedback.issue
            pattern_type = issue.pattern_type
            
            # Create training example
            training_example = {
                'issue_id': issue.id,
                'code_context': issue.code_context,
                'original_code': issue.original_code,
                'suggestion': issue.suggestion_text,
                'feedback_type': feedback.feedback_type,
                'feedback_value': feedback.feedback_value,
                'user_experience': feedback.user_experience_level,
                'modified_suggestion': feedback.modified_suggestion,
                'pattern_type': pattern_type,
                'severity': issue.severity,
                'ast_metadata': issue.ast_metadata,
                'location': issue.location
            }
            
            training_data[pattern_type].append(training_example)
        
        # Filter patterns with sufficient feedback
        filtered_training_data = {
            pattern: examples 
            for pattern, examples in training_data.items() 
            if len(examples) >= feedback_threshold
        }
        
        # Calculate statistics
        total_examples = sum(len(examples) for examples in filtered_training_data.values())
        positive_examples = sum(
            len([ex for ex in examples if ex['feedback_value'] > 0])
            for examples in filtered_training_data.values()
        )
        negative_examples = sum(
            len([ex for ex in examples if ex['feedback_value'] < 0])
            for examples in filtered_training_data.values()
        )
        
        return {
            'training_data': filtered_training_data,
            'metadata': {
                'total_examples': total_examples,
                'positive_examples': positive_examples,
                'negative_examples': negative_examples,
                'pattern_count': len(filtered_training_data),
                'patterns': list(filtered_training_data.keys()),
                'feedback_threshold': feedback_threshold,
                'min_validation_score': min_validation_score,
                'generated_at': datetime.utcnow().isoformat()
            }
        }
    
    def get_feedback_trends(
        self, 
        days: int = 30,
        pattern_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get feedback trends over time for monitoring model performance.
        
        Args:
            days: Number of days to analyze
            pattern_type: Optional filter by pattern type
            
        Returns:
            Dict containing trend data
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(FeedbackRecord).filter(
            FeedbackRecord.created_at >= start_date
        ).join(Issue)
        
        if pattern_type:
            query = query.filter(Issue.pattern_type == pattern_type)
        
        feedback_records = query.all()
        
        # Calculate daily trends
        daily_trends = defaultdict(lambda: {'accept': 0, 'reject': 0, 'modify': 0, 'ignore': 0})
        
        for record in feedback_records:
            date_str = record.created_at.strftime('%Y-%m-%d')
            daily_trends[date_str][record.feedback_type] += 1
        
        # Calculate acceptance rate trend
        acceptance_trends = {}
        for date_str, counts in daily_trends.items():
            total = sum(counts.values())
            if total > 0:
                acceptance_trends[date_str] = (counts['accept'] / total) * 100
        
        return {
            'daily_feedback_counts': dict(daily_trends),
            'acceptance_rate_trend': acceptance_trends,
            'total_feedback_period': len(feedback_records),
            'period_days': days,
            'pattern_type': pattern_type
        }