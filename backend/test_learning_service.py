"""
Unit tests for the LearningService class.

Tests cover:
- Feedback processing and training data preparation
- Fine-tuning job management and monitoring
- Model performance evaluation and comparison
- Model deployment and rollback functionality

Requirements covered: 3.1, 3.2, 3.3, 3.4, 4.2, 6.4
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.learning_service import (
    LearningService, TrainingDataset, FineTuningJob, PerformanceMetrics,
    ProcessingResult, LearningServiceError, InsufficientDataError
)
from app.models.feedback import FeedbackRecord, Issue, ModelVersion
from app.models.analysis import DirectAnalysis
from app.models.users import User
from app.schemas.feedback import FeedbackType


# Global fixtures for all test classes
@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock(spec=Session)

@pytest.fixture
def learning_service(mock_db):
    """Create a LearningService instance with mocked dependencies."""
    return LearningService(mock_db)

@pytest.fixture
def sample_feedback_record():
    """Create a sample feedback record for testing."""
    issue = Mock(spec=Issue)
    issue.id = "test_issue_123"
    issue.pattern_type = "unused_variable"
    issue.severity = "medium"
    issue.code_context = "def test_function():\n    unused_var = 42\n    return None"
    issue.original_code = "unused_var = 42"
    issue.suggestion_text = "Remove unused variable 'unused_var'"
    issue.suggested_fix = "# Remove this line"
    issue.location = {"line": 2, "column": 4}
    issue.ast_metadata = {"node_type": "assignment"}
    issue.confidence_score = 0.85
    
    feedback = Mock(spec=FeedbackRecord)
    feedback.id = 1
    feedback.issue_id = "test_issue_123"
    feedback.user_id = 1
    feedback.feedback_type = "accept"
    feedback.feedback_value = 1
    feedback.feedback_comment = "Good suggestion"
    feedback.modified_suggestion = None
    feedback.user_experience_level = "intermediate"
    feedback.is_validated = True
    feedback.validation_score = 0.9
    feedback.created_at = datetime.utcnow()
    feedback.context_data = {"ide": "vscode"}
    feedback.issue = issue
    
    return feedback

@pytest.fixture
def sample_model_version():
    """Create a sample model version for testing."""
    model = Mock(spec=ModelVersion)
    model.id = 1
    model.version_name = "gemini-pro-ft-20240115-120000"
    model.version_number = "1.0.1"
    model.base_model = "gemini-pro"
    model.training_data_size = 100
    model.deployment_status = "deployed"
    model.is_active = True
    model.is_production_ready = True
    model.acceptance_rate = 75.0
    model.performance_metrics = {"baseline_accuracy": 65.0}
    model.training_started_at = datetime.utcnow() - timedelta(hours=2)
    model.training_completed_at = datetime.utcnow() - timedelta(hours=1)
    model.deployed_at = datetime.utcnow() - timedelta(minutes=30)
    model.fine_tuning_job_id = "job_123456"
    model.get_performance_summary = Mock(return_value={
        'version': 'gemini-pro-ft-20240115-120000',
        'accuracy': 0.75,
        'acceptance_rate': 75.0,
        'f1_score': 0.8,
        'training_data_size': 100,
        'is_active': True,
        'deployment_status': 'deployed'
    })
    
    return model


class TestLearningService:
    """Test suite for LearningService functionality."""
    pass


class TestFeedbackProcessing:
    """Test feedback processing functionality."""
    
    def test_process_feedback_batch_success(self, learning_service, sample_feedback_record):
        """Test successful processing of feedback batch."""
        feedback_batch = [sample_feedback_record]
        
        result = learning_service.process_feedback_batch(feedback_batch)
        
        assert isinstance(result, ProcessingResult)
        assert result.processed_count == 1
        assert result.positive_count == 1
        assert result.negative_count == 0
        assert result.neutral_count == 0
        assert "unused_variable" in result.patterns_processed
        assert result.processing_time_seconds > 0
    
    def test_process_feedback_batch_with_invalid_feedback(self, learning_service):
        """Test processing batch with invalid feedback records."""
        # Create invalid feedback (no issue)
        invalid_feedback = Mock(spec=FeedbackRecord)
        invalid_feedback.id = 1
        invalid_feedback.issue = None
        
        feedback_batch = [invalid_feedback]
        result = learning_service.process_feedback_batch(feedback_batch)
        
        assert result.processed_count == 1  # Still processes but skips invalid ones
        assert result.positive_count == 0
        assert result.negative_count == 0
        assert result.neutral_count == 0
    
    def test_process_feedback_batch_empty(self, learning_service):
        """Test processing empty feedback batch."""
        with pytest.raises(LearningServiceError, match="Empty feedback batch provided"):
            learning_service.process_feedback_batch([])
    
    def test_create_training_example(self, learning_service, sample_feedback_record):
        """Test creation of training examples from feedback."""
        # Add analysis mock to the issue
        analysis_mock = Mock(spec=DirectAnalysis)
        analysis_mock.language = "python"
        analysis_mock.file_size_bytes = 1024
        analysis_mock.complexity_score = 5
        sample_feedback_record.issue.analysis = analysis_mock
        
        training_example = learning_service._create_training_example(sample_feedback_record)
        
        assert training_example is not None
        assert training_example["issue_id"] == "test_issue_123"
        assert training_example["feedback_id"] == 1
        assert training_example["pattern_type"] == "unused_variable"
        assert training_example["severity"] == "medium"
        assert training_example["code_context"] is not None
        assert training_example["suggestion_text"] is not None
        assert training_example["feedback_type"] == "accept"
        assert training_example["feedback_value"] == 1
        assert training_example["language"] == "python"


class TestTrainingDatasetPreparation:
    """Test training dataset preparation functionality."""
    
    def test_prepare_training_dataset_success(self, learning_service, mock_db, sample_feedback_record):
        """Test successful training dataset preparation."""
        # Create multiple feedback records with different patterns - need 100+ for min_training_examples
        feedback_records = []
        for i in range(120):  # Above min_training_examples threshold
            feedback = Mock(spec=FeedbackRecord)
            feedback.id = i
            feedback.issue = Mock(spec=Issue)
            feedback.issue.pattern_type = "unused_variable" if i < 60 else "code_complexity"
            feedback.issue.analysis = Mock(spec=DirectAnalysis)
            feedback.issue.analysis.language = "python"
            feedback.issue.analysis.file_size_bytes = 1024
            feedback.issue.analysis.complexity_score = 5
            feedback.feedback_value = 1 if i % 2 == 0 else -1
            feedback.is_validated = True
            feedback.validation_score = 0.9
            feedback.feedback_type = "accept" if i % 2 == 0 else "reject"
            feedback.feedback_comment = "Test comment"
            feedback.modified_suggestion = None
            feedback.user_experience_level = "intermediate"
            feedback.code_review_context = "team"
            feedback.created_at = datetime.utcnow()
            feedback_records.append(feedback)
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = feedback_records
        
        mock_db.query.return_value = mock_query
        
        dataset = learning_service.prepare_training_dataset()
        
        assert isinstance(dataset, TrainingDataset)
        assert len(dataset.positive_examples) > 0
        assert len(dataset.negative_examples) > 0
        assert dataset.metadata is not None
        assert "total_examples" in dataset.metadata
        assert "patterns_included" in dataset.metadata
    
    def test_prepare_training_dataset_insufficient_data(self, learning_service, mock_db):
        """Test dataset preparation with insufficient data."""
        # Mock database query returning insufficient data
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = []  # No feedback records
        
        mock_db.query.return_value = mock_query
        
        with pytest.raises(InsufficientDataError, match="Insufficient training data"):
            learning_service.prepare_training_dataset()
    
    def test_prepare_training_dataset_insufficient_pattern_data(self, learning_service, mock_db):
        """Test dataset preparation with insufficient data per pattern."""
        # Create feedback records but not enough per pattern (need 100+ total first)
        feedback_records = []
        for i in range(120):  # Above total threshold but below pattern threshold
            feedback = Mock(spec=FeedbackRecord)
            feedback.id = i
            feedback.issue = Mock(spec=Issue)
            feedback.issue.pattern_type = "unused_variable" if i < 5 else f"pattern_{i}"  # Only 5 for main pattern
            feedback.issue.analysis = Mock(spec=DirectAnalysis)
            feedback.feedback_value = 1
            feedback_records.append(feedback)
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = feedback_records
        
        mock_db.query.return_value = mock_query
        
        with pytest.raises(InsufficientDataError, match="No patterns have sufficient feedback"):
            learning_service.prepare_training_dataset()
    
    def test_generate_dataset_hash(self, learning_service):
        """Test dataset hash generation."""
        positive_examples = [{"feedback_id": 1}, {"feedback_id": 2}]
        negative_examples = [{"feedback_id": 3}]
        neutral_examples = [{"feedback_id": 4}]
        
        hash1 = learning_service._generate_dataset_hash(positive_examples, negative_examples, neutral_examples)
        hash2 = learning_service._generate_dataset_hash(positive_examples, negative_examples, neutral_examples)
        
        assert hash1 == hash2  # Same data should produce same hash
        assert len(hash1) == 64  # SHA-256 hash length


class TestFineTuningJobs:
    """Test fine-tuning job management functionality."""
    
    def test_trigger_fine_tuning_success(self, learning_service, mock_db):
        """Test successful fine-tuning job trigger."""
        # Create training dataset with sufficient data
        training_data = TrainingDataset(
            positive_examples=[{"example": "positive"}] * 60,
            negative_examples=[{"example": "negative"}] * 40,
            neutral_examples=[{"example": "neutral"}] * 20,
            metadata={"total_examples": 120}
        )
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock model version creation
        def refresh_side_effect(obj):
            obj.id = 1
        mock_db.refresh.side_effect = refresh_side_effect
        
        job = learning_service.trigger_fine_tuning(training_data)
        
        assert isinstance(job, FineTuningJob)
        assert job.status == "submitted"
        assert job.training_data_size == 120
        assert job.model_version_id == 1
        assert job.job_id is not None
        assert job.created_at is not None
        assert job.estimated_completion is not None
    
    def test_trigger_fine_tuning_insufficient_data(self, learning_service):
        """Test fine-tuning trigger with insufficient data."""
        training_data = TrainingDataset(
            positive_examples=[{"example": "positive"}] * 5,
            negative_examples=[{"example": "negative"}] * 3,
            neutral_examples=[{"example": "neutral"}] * 2,
            metadata={"total_examples": 10}
        )
        
        with pytest.raises(InsufficientDataError, match="Insufficient training examples"):
            learning_service.trigger_fine_tuning(training_data)
    
    def test_monitor_fine_tuning_job(self, learning_service, mock_db, sample_model_version):
        """Test fine-tuning job monitoring."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_model_version
        mock_db.query.return_value = mock_query
        
        job_status = learning_service.monitor_fine_tuning_job("job_123456")
        
        assert "job_id" in job_status
        assert job_status["job_id"] == "job_123456"
        assert job_status["model_version_id"] == 1
        assert "status" in job_status
        assert "progress" in job_status
        assert "training_data_size" in job_status
    
    def test_monitor_fine_tuning_job_not_found(self, learning_service, mock_db):
        """Test monitoring non-existent fine-tuning job."""
        # Mock database query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(LearningServiceError, match="Fine-tuning job .* not found"):
            learning_service.monitor_fine_tuning_job("nonexistent_job")


class TestModelPerformanceEvaluation:
    """Test model performance evaluation functionality."""
    
    def test_evaluate_model_performance(self, learning_service, mock_db, sample_model_version):
        """Test model performance evaluation."""
        # Mock model version query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_model_version
        mock_db.query.return_value = mock_query
        
        # Mock the _get_evaluation_dataset method
        evaluation_data = [
            {"feedback_value": 1, "pattern_type": "unused_variable"},
            {"feedback_value": -1, "pattern_type": "unused_variable"},
            {"feedback_value": 1, "pattern_type": "code_complexity"}
        ]
        learning_service._get_evaluation_dataset = Mock(return_value=evaluation_data)
        
        metrics = learning_service.evaluate_model_performance(1)
        
        assert isinstance(metrics, PerformanceMetrics)
        assert 0 <= metrics.accuracy_score <= 1
        assert 0 <= metrics.precision_score <= 1
        assert 0 <= metrics.recall_score <= 1
        assert 0 <= metrics.f1_score <= 1
        assert 0 <= metrics.acceptance_rate <= 100
        assert 0 <= metrics.rejection_rate <= 100
    
    def test_evaluate_model_performance_no_data(self, learning_service, mock_db, sample_model_version):
        """Test performance evaluation with no feedback data."""
        # Mock model version query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_model_version
        mock_db.query.return_value = mock_query
        
        # Mock empty evaluation dataset
        learning_service._get_evaluation_dataset = Mock(return_value=[])
        
        metrics = learning_service.evaluate_model_performance(1)
        
        assert metrics.accuracy_score == 0.0
        assert metrics.acceptance_rate == 0.0
    
    def test_evaluate_model_performance_not_found(self, learning_service, mock_db):
        """Test performance evaluation with non-existent model."""
        # Mock model version query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(LearningServiceError, match="Model version .* not found"):
            learning_service.evaluate_model_performance(999)
    
    def test_calculate_pattern_performance(self, learning_service):
        """Test pattern-specific performance calculation."""
        evaluation_data = [
            {"pattern_type": "unused_variable", "feedback_value": 1},
            {"pattern_type": "unused_variable", "feedback_value": 1},
            {"pattern_type": "unused_variable", "feedback_value": 1},
            {"pattern_type": "unused_variable", "feedback_value": 1},
            {"pattern_type": "unused_variable", "feedback_value": -1},
            {"pattern_type": "code_complexity", "feedback_value": 1},
            {"pattern_type": "code_complexity", "feedback_value": -1},
            {"pattern_type": "code_complexity", "feedback_value": -1},
            {"pattern_type": "code_complexity", "feedback_value": -1},
            {"pattern_type": "code_complexity", "feedback_value": -1},
        ]
        
        pattern_performance = learning_service._calculate_pattern_performance(evaluation_data)
        
        assert "unused_variable" in pattern_performance
        assert "code_complexity" in pattern_performance
        assert pattern_performance["unused_variable"]["acceptance_rate"] == 80.0
        assert pattern_performance["code_complexity"]["acceptance_rate"] == 20.0


class TestModelDeployment:
    """Test model deployment and rollback functionality."""
    
    def test_activate_model_version_success(self, learning_service, mock_db, sample_model_version):
        """Test successful model activation."""
        # Mock current active model
        current_active = Mock(spec=ModelVersion)
        current_active.is_active = True
        current_active.deployment_status = "deployed"
        
        # Mock database queries - need to handle two different queries
        call_count = 0
        def query_side_effect(model_class):
            nonlocal call_count
            call_count += 1
            query_mock = Mock()
            query_mock.filter.return_value = query_mock
            
            if call_count == 1:  # First call - get current active model
                query_mock.first.return_value = current_active
            else:  # Second call - get target model
                query_mock.first.return_value = sample_model_version
            
            return query_mock
        
        mock_db.query.side_effect = query_side_effect
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        activated_model = learning_service.activate_model_version(1)
        
        assert activated_model.is_active == True
        assert activated_model.deployment_status == "deployed"
        assert activated_model.is_production_ready == True
        # The current_active model should be deactivated
        assert current_active.is_active == False
        assert current_active.deployment_status == "retired"
    
    def test_activate_model_version_not_found(self, learning_service, mock_db):
        """Test activation of non-existent model."""
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(LearningServiceError, match="Model version .* not found"):
            learning_service.activate_model_version(999)
    
    def test_rollback_model_version_with_target(self, learning_service, mock_db, sample_model_version):
        """Test model version rollback to specific version."""
        # Mock target version
        target_version = Mock(spec=ModelVersion)
        target_version.id = 1
        target_version.version_name = "previous_version"
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = target_version
        mock_db.query.return_value = mock_query
        
        # Mock activate_model_version
        learning_service.activate_model_version = Mock(return_value=target_version)
        
        rolled_back_model = learning_service.rollback_model_version(1)
        
        assert rolled_back_model == target_version
        learning_service.activate_model_version.assert_called_once_with(1)
    
    def test_rollback_model_version_no_target(self, learning_service, mock_db):
        """Test model version rollback without specific target."""
        # Mock previous version query
        previous_version = Mock(spec=ModelVersion)
        previous_version.id = 1
        previous_version.version_name = "previous_version"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = previous_version
        mock_db.query.return_value = mock_query
        
        # Mock activate_model_version
        learning_service.activate_model_version = Mock(return_value=previous_version)
        
        rolled_back_model = learning_service.rollback_model_version()
        
        assert rolled_back_model == previous_version
        learning_service.activate_model_version.assert_called_once_with(1)
    
    def test_rollback_model_version_no_suitable_version(self, learning_service, mock_db):
        """Test rollback when no suitable version exists."""
        # Mock empty query result
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(LearningServiceError, match="No suitable model version found for rollback"):
            learning_service.rollback_model_version()


class TestModelVersionHistory:
    """Test model version history functionality."""
    
    def test_get_model_version_history(self, learning_service, mock_db, sample_model_version):
        """Test getting model version history."""
        # Create multiple model versions
        version1 = sample_model_version
        version2 = Mock(spec=ModelVersion)
        version2.id = 2
        version2.version_name = "gemini-pro-ft-20240116-120000"
        version2.version_number = "1.0.2"
        version2.base_model = "gemini-pro"
        version2.training_data_size = 150
        version2.is_active = False
        version2.deployment_status = "retired"
        version2.created_at = datetime.utcnow() - timedelta(days=1)
        version2.training_completed_at = datetime.utcnow() - timedelta(hours=23)
        version2.deployed_at = None
        version2.get_performance_summary = Mock(return_value={
            'version': 'gemini-pro-ft-20240116-120000',
            'accuracy': 0.72,
            'acceptance_rate': 72.0,
            'f1_score': 0.78,
            'training_data_size': 150,
            'is_active': False,
            'deployment_status': 'retired'
        })
        
        # Mock database query
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [version1, version2]
        mock_db.query.return_value = mock_query
        
        history = learning_service.get_model_version_history(limit=10)
        
        assert len(history) == 2
        assert history[0]['id'] == 1
        assert history[0]['version_name'] == "gemini-pro-ft-20240115-120000"
        assert history[0]['is_active'] == True
        assert history[1]['id'] == 2
        assert history[1]['is_active'] == False
    
    def test_get_model_version_history_exclude_inactive(self, learning_service, mock_db, sample_model_version):
        """Test getting model version history excluding inactive versions."""
        # Mock database query with filter
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_model_version]
        mock_db.query.return_value = mock_query
        
        history = learning_service.get_model_version_history(include_inactive=False)
        
        assert len(history) == 1
        assert history[0]['is_active'] == True
        
        # Verify filter was called
        mock_query.filter.assert_called_once()


class TestServiceConfiguration:
    """Test learning service configuration and initialization."""
    
    def test_learning_service_initialization(self, mock_db):
        """Test LearningService initialization with default parameters."""
        service = LearningService(mock_db)
        
        assert service.db == mock_db
        assert service.min_training_examples == 100
        assert service.min_pattern_examples == 10
        assert service.validation_split == 0.2
        assert isinstance(service.feedback_service, type(service.feedback_service))
    
    def test_learning_service_custom_thresholds(self, mock_db):
        """Test LearningService with custom threshold configuration."""
        service = LearningService(mock_db)
        service.min_training_examples = 200
        service.min_pattern_examples = 20
        service.validation_split = 0.3
        
        assert service.min_training_examples == 200
        assert service.min_pattern_examples == 20
        assert service.validation_split == 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])