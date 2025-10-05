from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean, Integer, Enum
from sqlalchemy.orm import relationship
import datetime
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class AnalysisStatus(str, PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class GitHubRepository(Base):
    """
    GitHub repository integration model for webhook and analysis management.
    
    Requirements covered: 8.1, 8.2, 8.6
    """
    __tablename__ = "github_repositories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    repo_url = Column(String(512), nullable=False, index=True)
    repo_name = Column(String(255), nullable=False, index=True)  # owner/repo format
    webhook_id = Column(String(255), nullable=True)  # GitHub webhook ID
    webhook_secret = Column(String(255), nullable=True)  # Webhook secret for verification
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Repository metadata
    default_branch = Column(String(100), default="main", nullable=False)
    repository_settings = Column(JSON, default=dict, nullable=False)
    
    # Access tokens and permissions
    access_token = Column(String(512), nullable=True)  # Encrypted GitHub access token
    permissions = Column(JSON, default=dict, nullable=False)  # Repository permissions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_webhook_received = Column(DateTime, nullable=True)

    # Relationships
    pr_analyses = relationship("PRAnalysis", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GitHubRepository(id={self.id}, repo_name={self.repo_name}, user_id={self.user_id})>"


class PRAnalysis(Base):
    """
    Pull request analysis model for tracking GitHub PR code analysis results.
    
    Requirements covered: 8.3, 8.4, 8.5
    """
    __tablename__ = "pr_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    repository_id = Column(String(36), ForeignKey("github_repositories.id"), nullable=False, index=True)
    pr_number = Column(Integer, nullable=False, index=True)
    pr_title = Column(String(500), nullable=True)
    pr_author = Column(String(255), nullable=True, index=True)
    
    # PR metadata
    head_sha = Column(String(64), nullable=False, index=True)
    base_sha = Column(String(64), nullable=False)
    head_branch = Column(String(255), nullable=False)
    base_branch = Column(String(255), nullable=False)
    
    # Analysis results
    analysis_results = Column(JSON, nullable=True)  # Complete analysis results
    issues_found = Column(Integer, default=0, nullable=False)
    errors_count = Column(Integer, default=0, nullable=False)
    warnings_count = Column(Integer, default=0, nullable=False)
    
    # GitHub integration
    issues_created = Column(JSON, default=list, nullable=False)  # List of created GitHub issue URLs
    comments_posted = Column(JSON, default=list, nullable=False)  # List of posted comment IDs
    
    # Status and timing
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String(1000), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    repository = relationship("GitHubRepository", overlaps="pr_analyses")

    def __repr__(self):
        return f"<PRAnalysis(id={self.id}, repository_id={self.repository_id}, pr_number={self.pr_number}, status={self.status})>"