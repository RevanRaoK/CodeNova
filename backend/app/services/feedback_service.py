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
            feedback_record = self._update_existing_feedback(existing_feedback, feedback_request)
        else:
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
        
        # Trigger learning pipeline integration
        self._trigger_learning_pipeline_update(
            user_id=user_id,
            issue_id=feedback_request.issue_id,
            feedback_type=feedback_request.feedback_type.value,
            feedback_value=self._get_feedback_value(feedback_request.feedback_type),
            feedback_comment=feedback_request.feedback_comment,
            modified_suggestion=feedback_request.modified_suggestion
        )
        
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
    
    def get_feedback_statistics_with_timeframe(
        self,
        user_id: int,
        timeframe: str = "week"
    ) -> Dict[str, Any]:
        """
        Get comprehensive feedback statistics with timeframe parameter.
        
        Args:
            user_id: User ID to get statistics for
            timeframe: Time period (week, month, quarter, year)
            
        Returns:
            Dict containing feedback statistics, trends, and model performance
            
        Requirements: 2.2, 2.3, 2.4, 2.5
        """
        # Calculate date range based on timeframe
        timeframe_days = {
            "week": 7,
            "month": 30,
            "quarter": 90,
            "year": 365
        }
        
        days = timeframe_days.get(timeframe, 7)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query for user's feedback in timeframe
        query = self.db.query(FeedbackRecord).filter(
            and_(
                FeedbackRecord.user_id == user_id,
                FeedbackRecord.created_at >= start_date
            )
        ).join(Issue)
        
        feedback_records = query.all()
        total_count = len(feedback_records)
        
        if total_count == 0:
            return self._empty_statistics_response(timeframe)
        
        # 1. Aggregation by feedback type (accept/reject/modify)
        feedback_by_type = self._aggregate_feedback_by_type(feedback_records)
        
        # 2. Calculate feedback trends over time periods
        feedback_trends = self._calculate_feedback_trends_over_time(feedback_records, days)
        
        # 3. Calculate model performance metrics based on feedback
        model_performance = self._calculate_model_performance_metrics(feedback_records)
        
        # 4. Additional statistics
        pattern_stats = self._calculate_pattern_feedback_stats(feedback_records)
        feedback_by_date = self._calculate_feedback_by_date(feedback_records)
        
        return {
            "timeframe": timeframe,
            "total_feedback": total_count,
            "feedback_by_type": feedback_by_type,
            "acceptance_rate": feedback_by_type["rates"]["acceptance_rate"],
            "rejection_rate": feedback_by_type["rates"]["rejection_rate"],
            "modification_rate": feedback_by_type["rates"]["modification_rate"],
            "feedback_trends": feedback_trends,
            "model_performance": model_performance,
            "pattern_feedback_stats": pattern_stats,
            "feedback_by_date": feedback_by_date,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _aggregate_feedback_by_type(self, feedback_records: List[FeedbackRecord]) -> Dict[str, Any]:
        """Aggregate feedback counts and rates by type."""
        total = len(feedback_records)
        counts = Counter(record.feedback_type for record in feedback_records)
        
        accept_count = counts.get('accept', 0)
        reject_count = counts.get('reject', 0)
        modify_count = counts.get('modify', 0)
        ignore_count = counts.get('ignore', 0)
        
        return {
            "counts": {
                "accept": accept_count,
                "reject": reject_count,
                "modify": modify_count,
                "ignore": ignore_count
            },
            "rates": {
                "acceptance_rate": round((accept_count / total) * 100, 2) if total > 0 else 0,
                "rejection_rate": round((reject_count / total) * 100, 2) if total > 0 else 0,
                "modification_rate": round((modify_count / total) * 100, 2) if total > 0 else 0,
                "ignore_rate": round((ignore_count / total) * 100, 2) if total > 0 else 0
            }
        }
    
    def _calculate_feedback_trends_over_time(
        self, 
        feedback_records: List[FeedbackRecord],
        days: int
    ) -> List[Dict[str, Any]]:
        """Calculate feedback trends over time periods."""
        # Group feedback by date
        daily_data = defaultdict(lambda: {
            'accept': 0, 
            'reject': 0, 
            'modify': 0, 
            'ignore': 0,
            'total': 0
        })
        
        for record in feedback_records:
            date_str = record.created_at.strftime('%Y-%m-%d')
            daily_data[date_str][record.feedback_type] += 1
            daily_data[date_str]['total'] += 1
        
        # Convert to list format with acceptance rates
        trends = []
        for date_str in sorted(daily_data.keys()):
            data = daily_data[date_str]
            total = data['total']
            
            trends.append({
                'date': date_str,
                'accept': data['accept'],
                'reject': data['reject'],
                'modify': data['modify'],
                'ignore': data['ignore'],
                'total': total,
                'acceptance_rate': round((data['accept'] / total) * 100, 2) if total > 0 else 0
            })
        
        return trends
    
    def _calculate_model_performance_metrics(
        self, 
        feedback_records: List[FeedbackRecord]
    ) -> List[Dict[str, Any]]:
        """Calculate model performance metrics based on feedback data."""
        total = len(feedback_records)
        if total == 0:
            return []
        
        # Count feedback types
        accept_count = sum(1 for r in feedback_records if r.feedback_type == 'accept')
        reject_count = sum(1 for r in feedback_records if r.feedback_type == 'reject')
        modify_count = sum(1 for r in feedback_records if r.feedback_type == 'modify')
        
        # Calculate average confidence scores for accepted suggestions
        accepted_with_confidence = [
            r.issue.confidence_score 
            for r in feedback_records 
            if r.feedback_type == 'accept' and r.issue and r.issue.confidence_score is not None
        ]
        avg_confidence = sum(accepted_with_confidence) / len(accepted_with_confidence) if accepted_with_confidence else 0
        
        # Calculate suggestion quality score (weighted metric)
        # Accept = 1.0, Modify = 0.5, Reject = 0.0
        quality_score = (accept_count + (modify_count * 0.5)) / total if total > 0 else 0
        
        # Calculate user engagement rate (non-ignore feedback)
        engaged_count = accept_count + reject_count + modify_count
        engagement_rate = (engaged_count / total) * 100 if total > 0 else 0
        
        # Get model version performance if available
        model_versions = self.db.query(ModelVersion).filter(
            ModelVersion.is_active == True
        ).order_by(desc(ModelVersion.created_at)).limit(1).all()
        
        current_model_accuracy = model_versions[0].accuracy_score if model_versions else None
        
        return [
            {
                "metric": "Acceptance Rate",
                "value": round((accept_count / total) * 100, 2),
                "unit": "%",
                "description": "Percentage of suggestions accepted by users"
            },
            {
                "metric": "Suggestion Quality Score",
                "value": round(quality_score * 100, 2),
                "unit": "%",
                "description": "Weighted quality metric (accept=100%, modify=50%, reject=0%)"
            },
            {
                "metric": "User Engagement Rate",
                "value": round(engagement_rate, 2),
                "unit": "%",
                "description": "Percentage of suggestions that received active feedback"
            },
            {
                "metric": "Average Confidence Score",
                "value": round(avg_confidence * 100, 2) if avg_confidence else 0,
                "unit": "%",
                "description": "Average AI confidence for accepted suggestions"
            },
            {
                "metric": "Model Accuracy",
                "value": round(current_model_accuracy * 100, 2) if current_model_accuracy else 0,
                "unit": "%",
                "description": "Current active model accuracy score"
            }
        ]
    
    def _empty_statistics_response(self, timeframe: str) -> Dict[str, Any]:
        """Return empty statistics response when no data is available."""
        return {
            "timeframe": timeframe,
            "total_feedback": 0,
            "feedback_by_type": {
                "counts": {"accept": 0, "reject": 0, "modify": 0, "ignore": 0},
                "rates": {
                    "acceptance_rate": 0.0,
                    "rejection_rate": 0.0,
                    "modification_rate": 0.0,
                    "ignore_rate": 0.0
                }
            },
            "acceptance_rate": 0.0,
            "rejection_rate": 0.0,
            "modification_rate": 0.0,
            "feedback_trends": [],
            "model_performance": [],
            "pattern_feedback_stats": {},
            "feedback_by_date": {},
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _trigger_learning_pipeline_update(
        self,
        user_id: int,
        issue_id: str,
        feedback_type: str,
        feedback_value: int,
        feedback_comment: Optional[str] = None,
        modified_suggestion: Optional[str] = None
    ) -> None:
        """
        Trigger learning pipeline update when feedback is received.
        
        This method connects feedback collection to the learning system with
        automatic pattern updates as required by the learning pipeline integration.
        
        Args:
            user_id: User ID
            issue_id: Issue ID
            feedback_type: Type of feedback
            feedback_value: Numeric feedback value
            feedback_comment: Optional feedback comment
            modified_suggestion: Optional modified suggestion
        
        Requirements: 8.5, 8.6, 8.10
        """
        try:
            # Import here to avoid circular imports
            from app.services.learning_pipeline_service import LearningPipelineService
            
            # Create learning pipeline service instance
            learning_service = LearningPipelineService(self.db)
            
            # Process feedback for learning
            learning_result = learning_service.process_feedback_for_learning(
                user_id=user_id,
                issue_id=issue_id,
                feedback_type=feedback_type,
                feedback_value=feedback_value,
                feedback_comment=feedback_comment,
                modified_suggestion=modified_suggestion
            )
            
            if learning_result.get("success"):
                logger.info(f"Learning pipeline updated for user {user_id}: {learning_result.get('updated_patterns', 0)} patterns updated")
            else:
                logger.warning(f"Learning pipeline update failed for user {user_id}: {learning_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            # Don't fail feedback recording if learning pipeline fails
            logger.error(f"Error triggering learning pipeline update: {e}")
            # Continue without raising exception to ensure feedback is still recorded