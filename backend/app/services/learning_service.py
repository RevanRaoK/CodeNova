"""
Learning pipeline service for AST-based feedback processing and model fine-tuning.

This service handles:
- Processing feedback data for model training
- Triggering and monitoring fine-tuning jobs
- Managing model versions and performance tracking
- Preparing training datasets from user feedback

Requirements covered: 3.1, 3.2, 3.3
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from collections import defaultdict, Counter
import json
import logging
import hashlib
from dataclasses import dataclass

from app.models.feedback import FeedbackRecord, Issue, ModelVersion
from app.models.analysis import DirectAnalysis
from app.models.users import User
from app.services.feedback_service import FeedbackService


logger = logging.getLogger(__name__)


@dataclass
class TrainingDataset:
    """Data class for training dataset information."""
    positive_examples: List[Dict[str, Any]]
    negative_examples: List[Dict[str, Any]]
    neutral_examples: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class FineTuningJob:
    """Data class for fine-tuning job information."""
    job_id: str
    model_version_id: int
    status: str
    training_data_size: int
    created_at: datetime
    estimated_completion: Optional[datetime] = None


@dataclass
class ProcessingResult:
    """Data class for feedback processing results."""
    processed_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    patterns_processed: List[str]
    processing_time_seconds: float


@dataclass
class PerformanceMetrics:
    """Data class for model performance metrics."""
    accuracy_score: float
    precision_score: float
    recall_score: float
    f1_score: float
    acceptance_rate: float
    rejection_rate: float
    improvement_over_baseline: float
    pattern_performance: Dict[str, Dict[str, float]]


class LearningServiceError(Exception):
    """Custom exception for learning service errors."""
    pass


class InsufficientDataError(LearningServiceError):
    """Exception raised when there's insufficient data for training."""
    pass


class LearningService:
    """Service class for managing the feedback learning pipeline and model fine-tuning."""
    
    def __init__(self, db: Session):
        self.db = db
        self.feedback_service = FeedbackService(db)
        self.min_training_examples = 100  # Minimum examples needed for training
        self.min_pattern_examples = 10    # Minimum examples per pattern
        self.validation_split = 0.2       # Percentage of data for validation
    
    def process_feedback_batch(
        self, 
        feedback_batch: List[FeedbackRecord],
        batch_id: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process a batch of feedback records for training data preparation.
        
        Args:
            feedback_batch: List of feedback records to process
            batch_id: Optional identifier for the batch
            
        Returns:
            ProcessingResult: Summary of processing results
            
        Requirements: 3.1, 3.2
        """
        start_time = datetime.utcnow()
        
        if not feedback_batch:
            raise LearningServiceError("Empty feedback batch provided")
        
        logger.info(f"Processing feedback batch with {len(feedback_batch)} records")
        
        # Categorize feedback by type
        positive_feedback = []
        negative_feedback = []
        neutral_feedback = []
        patterns_processed = set()
        
        for feedback in feedback_batch:
            if not feedback.issue:
                logger.warning(f"Feedback {feedback.id} has no associated issue, skipping")
                continue
            
            patterns_processed.add(feedback.issue.pattern_type)
            
            # Categorize based on feedback value
            if feedback.feedback_value > 0:
                positive_feedback.append(feedback)
            elif feedback.feedback_value < 0:
                negative_feedback.append(feedback)
            else:
                neutral_feedback.append(feedback)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log processing statistics
        logger.info(f"Processed {len(feedback_batch)} feedback records: "
                   f"{len(positive_feedback)} positive, {len(negative_feedback)} negative, "
                   f"{len(neutral_feedback)} neutral")
        
        return ProcessingResult(
            processed_count=len(feedback_batch),
            positive_count=len(positive_feedback),
            negative_count=len(negative_feedback),
            neutral_count=len(neutral_feedback),
            patterns_processed=list(patterns_processed),
            processing_time_seconds=processing_time
        )
    
    def prepare_training_dataset(
        self,
        min_feedback_per_pattern: int = None,
        include_neutral: bool = True,
        validation_split: float = None
    ) -> TrainingDataset:
        """
        Prepare a comprehensive training dataset from validated feedback.
        
        Args:
            min_feedback_per_pattern: Minimum feedback count per pattern (default: self.min_pattern_examples)
            include_neutral: Whether to include neutral feedback (modify/ignore)
            validation_split: Percentage for validation set (default: self.validation_split)
            
        Returns:
            TrainingDataset: Prepared training data with metadata
            
        Requirements: 3.1, 3.2
        """
        min_feedback_per_pattern = min_feedback_per_pattern or self.min_pattern_examples
        validation_split = validation_split or self.validation_split
        
        logger.info("Preparing training dataset from validated feedback")
        
        # Get validated feedback with associated issues
        validated_feedback = self.db.query(FeedbackRecord).filter(
            FeedbackRecord.is_validated == True
        ).join(Issue).join(DirectAnalysis).all()
        
        if len(validated_feedback) < self.min_training_examples:
            raise InsufficientDataError(
                f"Insufficient training data: {len(validated_feedback)} examples "
                f"(minimum required: {self.min_training_examples})"
            )
        
        # Group feedback by pattern type
        pattern_feedback = defaultdict(list)
        for feedback in validated_feedback:
            pattern_type = feedback.issue.pattern_type
            pattern_feedback[pattern_type].append(feedback)
        
        # Filter patterns with sufficient feedback
        filtered_patterns = {
            pattern: feedback_list 
            for pattern, feedback_list in pattern_feedback.items()
            if len(feedback_list) >= min_feedback_per_pattern
        }
        
        if not filtered_patterns:
            raise InsufficientDataError(
                f"No patterns have sufficient feedback (minimum: {min_feedback_per_pattern})"
            )
        
        # Prepare training examples
        positive_examples = []
        negative_examples = []
        neutral_examples = []
        
        for pattern, feedback_list in filtered_patterns.items():
            for feedback in feedback_list:
                training_example = self._create_training_example(feedback)
                
                if feedback.feedback_value > 0:
                    positive_examples.append(training_example)
                elif feedback.feedback_value < 0:
                    negative_examples.append(training_example)
                elif include_neutral:
                    neutral_examples.append(training_example)
        
        # Generate dataset metadata
        metadata = {
            'total_examples': len(positive_examples) + len(negative_examples) + len(neutral_examples),
            'positive_examples': len(positive_examples),
            'negative_examples': len(negative_examples),
            'neutral_examples': len(neutral_examples),
            'patterns_included': list(filtered_patterns.keys()),
            'pattern_counts': {
                pattern: len(feedback_list) 
                for pattern, feedback_list in filtered_patterns.items()
            },
            'validation_split': validation_split,
            'min_feedback_per_pattern': min_feedback_per_pattern,
            'include_neutral': include_neutral,
            'generated_at': datetime.utcnow().isoformat(),
            'dataset_hash': self._generate_dataset_hash(positive_examples, negative_examples, neutral_examples)
        }
        
        logger.info(f"Prepared training dataset: {metadata['total_examples']} examples, "
                   f"{len(filtered_patterns)} patterns")
        
        return TrainingDataset(
            positive_examples=positive_examples,
            negative_examples=negative_examples,
            neutral_examples=neutral_examples,
            metadata=metadata
        )
    
    def _create_training_example(self, feedback: FeedbackRecord) -> Dict[str, Any]:
        """Create a training example from a feedback record."""
        issue = feedback.issue
        analysis = issue.analysis
        
        return {
            'issue_id': issue.id,
            'feedback_id': feedback.id,
            'pattern_type': issue.pattern_type,
            'severity': issue.severity,
            'code_context': issue.code_context,
            'original_code': issue.original_code,
            'suggestion_text': issue.suggestion_text,
            'suggested_fix': issue.suggested_fix,
            'feedback_type': feedback.feedback_type,
            'feedback_value': feedback.feedback_value,
            'feedback_comment': feedback.feedback_comment,
            'modified_suggestion': feedback.modified_suggestion,
            'user_experience_level': feedback.user_experience_level,
            'code_review_context': feedback.code_review_context,
            'location': issue.location,
            'ast_metadata': issue.ast_metadata,
            'ast_node_type': issue.ast_node_type,
            'confidence_score': issue.confidence_score,
            'language': analysis.language if analysis else None,
            'file_size_bytes': analysis.file_size_bytes if analysis else None,
            'complexity_score': analysis.complexity_score if analysis else None,
            'created_at': feedback.created_at.isoformat(),
            'validation_score': feedback.validation_score
        }
    
    def _generate_dataset_hash(
        self, 
        positive_examples: List[Dict[str, Any]], 
        negative_examples: List[Dict[str, Any]], 
        neutral_examples: List[Dict[str, Any]]
    ) -> str:
        """Generate a hash for the dataset to track versions."""
        all_examples = positive_examples + negative_examples + neutral_examples
        example_ids = sorted([ex['feedback_id'] for ex in all_examples])
        hash_input = json.dumps(example_ids, sort_keys=True)
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def trigger_fine_tuning(
        self, 
        training_data: TrainingDataset,
        base_model: str = "gemini-pro",
        training_config: Optional[Dict[str, Any]] = None
    ) -> FineTuningJob:
        """
        Trigger a fine-tuning job with the prepared training data.
        
        Args:
            training_data: Prepared training dataset
            base_model: Base model to fine-tune
            training_config: Optional training configuration parameters
            
        Returns:
            FineTuningJob: Information about the created fine-tuning job
            
        Requirements: 3.1, 3.3
        """
        if training_data.metadata['total_examples'] < self.min_training_examples:
            raise InsufficientDataError(
                f"Insufficient training examples: {training_data.metadata['total_examples']} "
                f"(minimum required: {self.min_training_examples})"
            )
        
        logger.info(f"Triggering fine-tuning job with {training_data.metadata['total_examples']} examples")
        
        # Create model version record
        version_name = f"{base_model}-ft-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        model_version = ModelVersion(
            version_name=version_name,
            version_number="1.0.0",  # Will be updated based on previous versions
            base_model=base_model,
            model_type="gemini",
            training_data_size=training_data.metadata['total_examples'],
            training_config=training_config or {},
            model_metadata=training_data.metadata,
            deployment_status="training",
            is_active=False,
            is_production_ready=False,
            training_started_at=datetime.utcnow()
        )
        
        self.db.add(model_version)
        self.db.commit()
        self.db.refresh(model_version)
        
        # Generate job ID (in real implementation, this would come from the ML platform)
        job_id = f"ft-job-{model_version.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Update model version with job ID
        model_version.fine_tuning_job_id = job_id
        self.db.commit()
        
        # In a real implementation, this would submit the job to a ML platform
        # For now, we'll simulate the job creation
        logger.info(f"Created fine-tuning job {job_id} for model version {model_version.id}")
        
        # Estimate completion time (this would come from the ML platform)
        estimated_completion = datetime.utcnow() + timedelta(hours=2)
        
        return FineTuningJob(
            job_id=job_id,
            model_version_id=model_version.id,
            status="submitted",
            training_data_size=training_data.metadata['total_examples'],
            created_at=datetime.utcnow(),
            estimated_completion=estimated_completion
        )
    
    def monitor_fine_tuning_job(self, job_id: str) -> Dict[str, Any]:
        """
        Monitor the status of a fine-tuning job.
        
        Args:
            job_id: Fine-tuning job identifier
            
        Returns:
            Dict containing job status and progress information
            
        Requirements: 3.3
        """
        # Find the model version associated with this job
        model_version = self.db.query(ModelVersion).filter(
            ModelVersion.fine_tuning_job_id == job_id
        ).first()
        
        if not model_version:
            raise LearningServiceError(f"Fine-tuning job {job_id} not found")
        
        # In a real implementation, this would query the ML platform
        # For now, we'll simulate job monitoring
        job_status = self._simulate_job_status(model_version)
        
        return {
            'job_id': job_id,
            'model_version_id': model_version.id,
            'status': job_status['status'],
            'progress': job_status['progress'],
            'training_data_size': model_version.training_data_size,
            'created_at': model_version.created_at.isoformat(),
            'training_started_at': model_version.training_started_at.isoformat() if model_version.training_started_at else None,
            'estimated_completion': job_status.get('estimated_completion'),
            'current_metrics': job_status.get('current_metrics', {}),
            'error_message': job_status.get('error_message')
        }
    
    def _simulate_job_status(self, model_version: ModelVersion) -> Dict[str, Any]:
        """Simulate job status for demonstration purposes."""
        # In a real implementation, this would query the actual ML platform
        elapsed_time = datetime.utcnow() - (model_version.training_started_at or model_version.created_at)
        elapsed_minutes = elapsed_time.total_seconds() / 60
        
        if elapsed_minutes < 5:
            return {
                'status': 'initializing',
                'progress': 0.1,
                'estimated_completion': (datetime.utcnow() + timedelta(hours=2)).isoformat()
            }
        elif elapsed_minutes < 30:
            progress = min(0.8, elapsed_minutes / 120)  # 2 hours total
            return {
                'status': 'training',
                'progress': progress,
                'current_metrics': {
                    'loss': 0.5 - (progress * 0.3),
                    'accuracy': 0.6 + (progress * 0.2)
                },
                'estimated_completion': (datetime.utcnow() + timedelta(minutes=120-elapsed_minutes)).isoformat()
            }
        else:
            return {
                'status': 'completed',
                'progress': 1.0,
                'current_metrics': {
                    'final_loss': 0.2,
                    'final_accuracy': 0.85
                }
            }
    
    def evaluate_model_performance(
        self, 
        model_version_id: int,
        evaluation_data: Optional[List[Dict[str, Any]]] = None
    ) -> PerformanceMetrics:
        """
        Evaluate the performance of a fine-tuned model.
        
        Args:
            model_version_id: ID of the model version to evaluate
            evaluation_data: Optional evaluation dataset (uses validation split if not provided)
            
        Returns:
            PerformanceMetrics: Comprehensive performance metrics
            
        Requirements: 3.4, 4.2
        """
        model_version = self.db.query(ModelVersion).filter(
            ModelVersion.id == model_version_id
        ).first()
        
        if not model_version:
            raise LearningServiceError(f"Model version {model_version_id} not found")
        
        logger.info(f"Evaluating performance for model version {model_version.version_name}")
        
        # If no evaluation data provided, use recent feedback as evaluation set
        if not evaluation_data:
            evaluation_data = self._get_evaluation_dataset(model_version)
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics(evaluation_data, model_version)
        
        # Update model version with performance metrics
        model_version.accuracy_score = metrics.accuracy_score
        model_version.precision_score = metrics.precision_score
        model_version.recall_score = metrics.recall_score
        model_version.f1_score = metrics.f1_score
        model_version.acceptance_rate = metrics.acceptance_rate
        model_version.rejection_rate = metrics.rejection_rate
        model_version.improvement_score = metrics.improvement_over_baseline
        
        # Store detailed performance metrics
        model_version.performance_metrics = {
            'accuracy': metrics.accuracy_score,
            'precision': metrics.precision_score,
            'recall': metrics.recall_score,
            'f1_score': metrics.f1_score,
            'acceptance_rate': metrics.acceptance_rate,
            'rejection_rate': metrics.rejection_rate,
            'improvement_over_baseline': metrics.improvement_over_baseline,
            'pattern_performance': metrics.pattern_performance,
            'evaluation_date': datetime.utcnow().isoformat(),
            'evaluation_data_size': len(evaluation_data)
        }
        
        self.db.commit()
        
        logger.info(f"Model evaluation completed: accuracy={metrics.accuracy_score:.3f}, "
                   f"acceptance_rate={metrics.acceptance_rate:.3f}")
        
        return metrics
    
    def _get_evaluation_dataset(self, model_version: ModelVersion) -> List[Dict[str, Any]]:
        """Get evaluation dataset for model performance assessment."""
        # Use recent feedback data that wasn't used in training
        cutoff_date = model_version.training_started_at or model_version.created_at
        
        recent_feedback = self.db.query(FeedbackRecord).filter(
            and_(
                FeedbackRecord.created_at > cutoff_date,
                FeedbackRecord.is_validated == True
            )
        ).join(Issue).limit(200).all()  # Limit evaluation set size
        
        return [self._create_training_example(feedback) for feedback in recent_feedback]
    
    def _calculate_performance_metrics(
        self, 
        evaluation_data: List[Dict[str, Any]], 
        model_version: ModelVersion
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if not evaluation_data:
            # Return default metrics if no evaluation data
            return PerformanceMetrics(
                accuracy_score=0.0,
                precision_score=0.0,
                recall_score=0.0,
                f1_score=0.0,
                acceptance_rate=0.0,
                rejection_rate=0.0,
                improvement_over_baseline=0.0,
                pattern_performance={}
            )
        
        # Calculate basic metrics
        total_examples = len(evaluation_data)
        positive_examples = [ex for ex in evaluation_data if ex['feedback_value'] > 0]
        negative_examples = [ex for ex in evaluation_data if ex['feedback_value'] < 0]
        
        acceptance_rate = (len(positive_examples) / total_examples) * 100 if total_examples > 0 else 0
        rejection_rate = (len(negative_examples) / total_examples) * 100 if total_examples > 0 else 0
        
        # Simulate accuracy metrics (in real implementation, these would come from model evaluation)
        accuracy_score = min(0.95, 0.6 + (acceptance_rate / 100) * 0.3)
        precision_score = min(0.95, 0.65 + (acceptance_rate / 100) * 0.25)
        recall_score = min(0.95, 0.7 + (acceptance_rate / 100) * 0.2)
        f1_score = 2 * (precision_score * recall_score) / (precision_score + recall_score) if (precision_score + recall_score) > 0 else 0
        
        # Calculate improvement over baseline (assuming baseline acceptance rate of 60%)
        baseline_acceptance = 60.0
        improvement_over_baseline = acceptance_rate - baseline_acceptance
        
        # Calculate pattern-specific performance
        pattern_performance = self._calculate_pattern_performance(evaluation_data)
        
        return PerformanceMetrics(
            accuracy_score=round(accuracy_score, 3),
            precision_score=round(precision_score, 3),
            recall_score=round(recall_score, 3),
            f1_score=round(f1_score, 3),
            acceptance_rate=round(acceptance_rate, 2),
            rejection_rate=round(rejection_rate, 2),
            improvement_over_baseline=round(improvement_over_baseline, 2),
            pattern_performance=pattern_performance
        )
    
    def _calculate_pattern_performance(self, evaluation_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculate performance metrics by pattern type."""
        pattern_data = defaultdict(list)
        
        # Group by pattern type
        for example in evaluation_data:
            pattern_type = example['pattern_type']
            pattern_data[pattern_type].append(example)
        
        pattern_performance = {}
        
        for pattern_type, examples in pattern_data.items():
            if len(examples) < 5:  # Skip patterns with too few examples
                continue
            
            total = len(examples)
            positive = len([ex for ex in examples if ex['feedback_value'] > 0])
            negative = len([ex for ex in examples if ex['feedback_value'] < 0])
            
            acceptance_rate = (positive / total) * 100 if total > 0 else 0
            rejection_rate = (negative / total) * 100 if total > 0 else 0
            
            pattern_performance[pattern_type] = {
                'acceptance_rate': round(acceptance_rate, 2),
                'rejection_rate': round(rejection_rate, 2),
                'total_examples': total,
                'confidence': min(1.0, total / 20)  # Confidence based on sample size
            }
        
        return pattern_performance
    
    def get_model_version_history(
        self, 
        limit: int = 10,
        include_inactive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get history of model versions with performance metrics.
        
        Args:
            limit: Maximum number of versions to return
            include_inactive: Whether to include inactive model versions
            
        Returns:
            List of model version information with performance data
        """
        query = self.db.query(ModelVersion)
        
        if not include_inactive:
            query = query.filter(ModelVersion.is_active == True)
        
        model_versions = query.order_by(desc(ModelVersion.created_at)).limit(limit).all()
        
        return [
            {
                'id': version.id,
                'version_name': version.version_name,
                'version_number': version.version_number,
                'base_model': version.base_model,
                'training_data_size': version.training_data_size,
                'is_active': version.is_active,
                'deployment_status': version.deployment_status,
                'performance_summary': version.get_performance_summary(),
                'created_at': version.created_at.isoformat(),
                'training_completed_at': version.training_completed_at.isoformat() if version.training_completed_at else None,
                'deployed_at': version.deployed_at.isoformat() if version.deployed_at else None
            }
            for version in model_versions
        ]
    
    def activate_model_version(self, model_version_id: int) -> ModelVersion:
        """
        Activate a model version for production use.
        
        Args:
            model_version_id: ID of the model version to activate
            
        Returns:
            ModelVersion: The activated model version
            
        Requirements: 4.2, 6.4
        """
        # Deactivate current active model
        current_active = self.db.query(ModelVersion).filter(
            ModelVersion.is_active == True
        ).first()
        
        if current_active:
            current_active.is_active = False
            current_active.deployment_status = "retired"
            current_active.retired_at = datetime.utcnow()
        
        # Activate new model version
        new_active = self.db.query(ModelVersion).filter(
            ModelVersion.id == model_version_id
        ).first()
        
        if not new_active:
            raise LearningServiceError(f"Model version {model_version_id} not found")
        
        new_active.is_active = True
        new_active.deployment_status = "deployed"
        new_active.deployed_at = datetime.utcnow()
        new_active.is_production_ready = True
        
        self.db.commit()
        self.db.refresh(new_active)
        
        logger.info(f"Activated model version {new_active.version_name}")
        
        return new_active
    
    def rollback_model_version(self, target_version_id: Optional[int] = None) -> ModelVersion:
        """
        Rollback to a previous model version.
        
        Args:
            target_version_id: Specific version to rollback to (defaults to previous active)
            
        Returns:
            ModelVersion: The rolled back model version
            
        Requirements: 4.2, 6.4
        """
        if target_version_id:
            target_version = self.db.query(ModelVersion).filter(
                ModelVersion.id == target_version_id
            ).first()
        else:
            # Find the most recent previously active version
            target_version = self.db.query(ModelVersion).filter(
                and_(
                    ModelVersion.is_active == False,
                    ModelVersion.deployment_status == "retired"
                )
            ).order_by(desc(ModelVersion.retired_at)).first()
        
        if not target_version:
            raise LearningServiceError("No suitable model version found for rollback")
        
        logger.info(f"Rolling back to model version {target_version.version_name}")
        
        return self.activate_model_version(target_version.id)