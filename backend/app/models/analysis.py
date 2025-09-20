from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime
import uuid

class Analysis(Base):
    """Repository-based analysis model for analyzing entire repositories."""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    commit_hash = Column(String(64), nullable=False)
    status = Column(String(20), default="pending")  # pending, in_progress, completed, failed
    results = Column(JSON, nullable=True)  # Store the full analysis results
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    repository = relationship("Repository", back_populates="analyses")

class DirectAnalysis(Base):
    """
    Direct code analysis model for storing direct code analysis results.
    
    This model stores analysis results for code submitted directly through
    the /analyze-code endpoint, separate from repository-based analyses.
    
    Requirements covered: 2.1, 5.1, 5.2
    """
    __tablename__ = "direct_analyses"

    # Use UUID as primary key for better security and uniqueness
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # User association for analysis history tracking
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Code content and metadata
    code_content = Column(Text, nullable=False)  # The analyzed code
    language = Column(String(50), nullable=False, index=True)  # Programming language
    filename = Column(String(255), nullable=True)  # Optional filename for context
    
    # Analysis status and timing
    status = Column(String(20), default="pending", index=True)  # pending, in_progress, completed, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Analysis results stored as JSON
    results = Column(JSON, nullable=True)  # Complete analysis results
    
    # Code metrics (denormalized for easier querying)
    lines_of_code = Column(Integer, nullable=True)
    complexity_score = Column(Integer, nullable=True)
    maintainability_index = Column(Integer, nullable=True)
    issues_count = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    warnings_count = Column(Integer, default=0)
    
    # File size information
    file_size_bytes = Column(Integer, nullable=True)
    
    # Error information for failed analyses
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="direct_analyses")

    def __repr__(self):
        return f"<DirectAnalysis(id={self.id}, user_id={self.user_id}, language={self.language}, status={self.status})>"
