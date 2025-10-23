"""
File batch models for multi-file upload and analysis tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
from enum import Enum

from app.core.database import Base


class BatchStatus(str, Enum):
    """Batch processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some files succeeded, some failed


class FileStatus(str, Enum):
    """Individual file processing status enumeration."""
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileBatch(Base):
    """
    Model for tracking multi-file upload batches.
    
    This model tracks the overall batch processing status and metadata
    for multi-file upload operations.
    """
    __tablename__ = "file_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Batch metadata
    total_files = Column(Integer, nullable=False)
    processed_files = Column(Integer, default=0)
    successful_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    
    # Status tracking
    status = Column(String(20), default=BatchStatus.PENDING, index=True)
    
    # Results and errors
    combined_results = Column(JSON)  # Combined analysis results
    error_details = Column(JSON)     # Error information
    processing_log = Column(JSON)    # Processing steps log
    
    # Timing information
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Processing metrics
    total_size_bytes = Column(Integer, default=0)
    processing_time_seconds = Column(Float)
    estimated_completion_time = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="file_batches")
    batch_files = relationship("BatchFile", back_populates="batch", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FileBatch(id={self.id}, user_id={self.user_id}, status={self.status}, files={self.total_files})>"
    
    @property
    def progress_percentage(self) -> float:
        """Calculate batch processing progress as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if batch processing is complete."""
        return self.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.PARTIAL]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.processed_files == 0:
            return 0.0
        return (self.successful_files / self.processed_files) * 100


class BatchFile(Base):
    """
    Model for tracking individual files within a batch.
    
    This model tracks the processing status and results for each file
    in a multi-file upload batch.
    """
    __tablename__ = "batch_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("file_batches.id"), nullable=False, index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    content_type = Column(String(100))
    language = Column(String(50))
    
    # Processing information
    file_index = Column(Integer, nullable=False)  # Order in the batch
    status = Column(String(20), default=FileStatus.PENDING, index=True)
    
    # File content and storage
    file_content = Column(Text)  # Store file content for analysis
    storage_path = Column(String(512))  # Path in file storage system
    stored_file_id = Column(String(36), ForeignKey("stored_files.id"))
    
    # Analysis results
    analysis_id = Column(String(36))  # Reference to analysis result
    issues_count = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    warnings_count = Column(Integer, default=0)
    suggestions_count = Column(Integer, default=0)
    
    # Analysis data
    analysis_results = Column(JSON)  # Detailed analysis results
    analysis_metrics = Column(JSON)  # Code metrics
    analysis_summary = Column(Text)  # Human-readable summary
    
    # Error handling
    error_message = Column(Text)
    error_code = Column(String(50))
    error_details = Column(JSON)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_processing_at = Column(DateTime)
    completed_at = Column(DateTime)
    processing_time_seconds = Column(Float)
    
    # Relationships
    batch = relationship("FileBatch", back_populates="batch_files")
    stored_file = relationship("StoredFile")
    
    def __repr__(self):
        return f"<BatchFile(id={self.id}, filename={self.filename}, status={self.status})>"
    
    @property
    def is_complete(self) -> bool:
        """Check if file processing is complete."""
        return self.status in [FileStatus.COMPLETED, FileStatus.FAILED]
    
    @property
    def has_analysis_results(self) -> bool:
        """Check if file has analysis results."""
        return self.analysis_results is not None and len(self.analysis_results) > 0
    
    @property
    def file_size_kb(self) -> float:
        """Get file size in KB."""
        return self.file_size_bytes / 1024 if self.file_size_bytes else 0.0
    
    @property
    def lines_count(self) -> int:
        """Get number of lines in the file."""
        if not self.file_content:
            return 0
        return len(self.file_content.split('\n'))


# Add relationship to User model (this would be added to the User model)
# user.file_batches = relationship("FileBatch", back_populates="user")