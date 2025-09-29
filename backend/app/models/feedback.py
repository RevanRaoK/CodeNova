"""
Feedback system models for AST-based code analysis and learning pipeline.

This module contains the database models for:
- Issue tracking with unique identifiers
- User feedback collection and storage
- Model version tracking for fine-tuning

Requirements covered: 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.4, 4.2
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Boolean, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime


class Issue(Base):
    """
    Issue model for tracking unique code issues detected by AST analysis.
    
    Each issue represents a specific code problem or suggestion with a unique
    deterministic ID that allows for consistent tracking across analysis runs.
    
    Requirements covered: 1.3, 2.4
    """
    __tablename__ = "issues"

    # Deterministic hash-based ID (64 characters for SHA-256)
    id = Column(String(64), primary_key=True, index=True)
    
    # Foreign key to DirectAnalysis
    analysis_id = Column(String(36), ForeignKey("direct_analyses.id"), nullable=False, index=True)
    
    # Issue classification and metadata
    pattern_type = Column(String(100), nullable=False, index=True)  # Type of code pattern detected
    severity = Column(String(20), nullable=False, index=True)  # info, low, medium, high, critical
    category = Column(String(50), nullable=True, index=True)  # Optional categorization
    
    # Location information in the code
    location = Column(JSON, nullable=False)  # {line, column, start_line, end_line, context}
    
    # Issue content and suggestions
    suggestion_text = Column(Text, nullable=False)  # The AI-generated suggestion
    code_context = Column(Text, nullable=False)  # Relevant code snippet
    original_code = Column(Text, nullable=True)  # Original problematic code
    suggested_fix = Column(Text, nullable=True)  # Suggested code replacement
    
    # AST-specific metadata
    ast_node_type = Column(String(100), nullable=True)  # Type of AST node
    ast_metadata = Column(JSON, nullable=True)  # Additional AST information
    
    # Issue lifecycle tracking
    status = Column(String(20), default="active", index=True)  # active, resolved, ignored
    confidence_score = Column(Float, nullable=True)  # AI confidence in the suggestion
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    analysis = relationship("DirectAnalysis", back_populates="issues")
    feedback_records = relationship("FeedbackRecord", back_populates="issue", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_issues_analysis_pattern', 'analysis_id', 'pattern_type'),
        Index('idx_issues_severity_status', 'severity', 'status'),
        Index('idx_issues_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<Issue(id={self.id[:8]}..., pattern_type={self.pattern_type}, severity={self.severity})>"


class FeedbackRecord(Base):
    """
    FeedbackRecord model for storing user feedback on AI suggestions.
    
    Captures user acceptance/rejection of suggestions along with contextual
    information for model learning and improvement.
    
    Requirements covered: 2.1, 2.2, 2.3, 2.4
    """
    __tablename__ = "feedback_records"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    issue_id = Column(String(64), ForeignKey("issues.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Feedback classification
    feedback_type = Column(String(20), nullable=False, index=True)  # accept, reject, modify, ignore
    feedback_value = Column(Integer, nullable=False)  # 1 for positive, -1 for negative, 0 for neutral
    
    # Feedback content
    feedback_comment = Column(Text, nullable=True)  # Optional user comment
    modified_suggestion = Column(Text, nullable=True)  # User's modified version if applicable
    
    # Context information for learning
    context_data = Column(JSON, nullable=True)  # Additional context (IDE, project type, etc.)
    user_experience_level = Column(String(20), nullable=True)  # beginner, intermediate, expert
    code_review_context = Column(String(50), nullable=True)  # personal, team, production
    
    # Feedback quality and validation
    is_validated = Column(Boolean, default=False)  # Whether feedback has been validated
    validation_score = Column(Float, nullable=True)  # Quality score for the feedback
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    issue = relationship("Issue", back_populates="feedback_records")
    user = relationship("User", back_populates="feedback_records")

    # Indexes for performance
    __table_args__ = (
        Index('idx_feedback_issue_user', 'issue_id', 'user_id'),
        Index('idx_feedback_type_value', 'feedback_type', 'feedback_value'),
        Index('idx_feedback_created_at', 'created_at'),
        Index('idx_feedback_validated', 'is_validated'),
    )

    def __repr__(self):
        return f"<FeedbackRecord(id={self.id}, issue_id={self.issue_id[:8]}..., feedback_type={self.feedback_type})>"


class ModelVersion(Base):
    """
    ModelVersion model for tracking AI model fine-tuning iterations and performance.
    
    Maintains version history, performance metrics, and deployment status
    of fine-tuned models based on user feedback.
    
    Requirements covered: 3.1, 3.4, 4.2
    """
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Version identification
    version_name = Column(String(100), unique=True, nullable=False, index=True)
    version_number = Column(String(20), nullable=False)  # Semantic versioning (e.g., "1.2.3")
    
    # Model information
    base_model = Column(String(100), nullable=False)  # Base model used for fine-tuning
    model_type = Column(String(50), nullable=False, default="gemini")  # Model family
    
    # Training information
    training_data_size = Column(Integer, nullable=False)  # Number of training examples
    training_duration_minutes = Column(Float, nullable=True)  # Training time
    fine_tuning_job_id = Column(String(255), nullable=True, index=True)  # External job ID
    
    # Performance metrics
    performance_metrics = Column(JSON, nullable=True)  # Detailed performance data
    accuracy_score = Column(Float, nullable=True)  # Overall accuracy
    precision_score = Column(Float, nullable=True)  # Precision metric
    recall_score = Column(Float, nullable=True)  # Recall metric
    f1_score = Column(Float, nullable=True)  # F1 score
    
    # Feedback-based metrics
    acceptance_rate = Column(Float, nullable=True)  # User acceptance rate
    rejection_rate = Column(Float, nullable=True)  # User rejection rate
    improvement_score = Column(Float, nullable=True)  # Improvement over previous version
    
    # Deployment status
    is_active = Column(Boolean, default=False, index=True)  # Currently deployed model
    is_production_ready = Column(Boolean, default=False)  # Ready for production use
    deployment_status = Column(String(20), default="training")  # training, testing, deployed, retired
    
    # Configuration and metadata
    training_config = Column(JSON, nullable=True)  # Training hyperparameters and settings
    model_metadata = Column(JSON, nullable=True)  # Additional model information
    
    # Quality assurance
    validation_results = Column(JSON, nullable=True)  # Validation test results
    a_b_test_results = Column(JSON, nullable=True)  # A/B testing results if applicable
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    training_started_at = Column(DateTime, nullable=True)
    training_completed_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    retired_at = Column(DateTime, nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_model_version_active', 'is_active'),
        Index('idx_model_version_status', 'deployment_status'),
        Index('idx_model_version_created', 'created_at'),
        Index('idx_model_version_performance', 'accuracy_score', 'acceptance_rate'),
    )

    def __repr__(self):
        return f"<ModelVersion(id={self.id}, version_name={self.version_name}, is_active={self.is_active})>"

    @property
    def is_better_than_baseline(self) -> bool:
        """Check if this model version performs better than baseline metrics."""
        if not self.performance_metrics:
            return False
        
        baseline_accuracy = self.performance_metrics.get('baseline_accuracy', 0.0)
        return (self.accuracy_score or 0.0) > baseline_accuracy

    def get_performance_summary(self) -> dict:
        """Get a summary of key performance metrics."""
        return {
            'version': self.version_name,
            'accuracy': self.accuracy_score,
            'acceptance_rate': self.acceptance_rate,
            'f1_score': self.f1_score,
            'training_data_size': self.training_data_size,
            'is_active': self.is_active,
            'deployment_status': self.deployment_status
        }