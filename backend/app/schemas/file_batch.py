"""
Pydantic schemas for file batch operations.

These schemas handle validation and serialization for multi-file upload
and batch processing operations.

Requirements covered: 1.1, 1.2, 1.3, 1.4, 1.5
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class BatchStatusEnum(str, Enum):
    """Batch processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class FileStatusEnum(str, Enum):
    """Individual file processing status enumeration."""
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


# BatchFile Schemas

class BatchFileBase(BaseModel):
    """Base schema for batch file."""
    filename: str = Field(..., min_length=1, max_length=255)
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: int = Field(..., ge=0)
    content_type: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=50)


class BatchFileCreate(BatchFileBase):
    """Schema for creating a batch file entry."""
    batch_id: str
    file_index: int = Field(..., ge=0)
    file_content: Optional[str] = None
    storage_path: Optional[str] = None


class BatchFileUpdate(BaseModel):
    """Schema for updating a batch file."""
    status: Optional[FileStatusEnum] = None
    analysis_id: Optional[str] = None
    issues_count: Optional[int] = Field(None, ge=0)
    errors_count: Optional[int] = Field(None, ge=0)
    warnings_count: Optional[int] = Field(None, ge=0)
    suggestions_count: Optional[int] = Field(None, ge=0)
    analysis_results: Optional[Dict[str, Any]] = None
    analysis_metrics: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    processing_time_seconds: Optional[float] = Field(None, ge=0)


class BatchFileResponse(BatchFileBase):
    """Schema for batch file response."""
    id: str
    batch_id: str
    file_index: int
    status: str
    language: Optional[str] = None
    analysis_id: Optional[str] = None
    issues_count: int
    errors_count: int
    warnings_count: int
    suggestions_count: int
    analysis_results: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    
    class Config:
        from_attributes = True


class BatchFileDetailResponse(BatchFileResponse):
    """Detailed schema for batch file with full analysis results."""
    file_content: Optional[str] = None
    storage_path: Optional[str] = None
    analysis_metrics: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


# FileBatch Schemas

class FileBatchBase(BaseModel):
    """Base schema for file batch."""
    total_files: int = Field(..., ge=1)


class FileBatchCreate(FileBatchBase):
    """Schema for creating a file batch."""
    user_id: int


class FileBatchUpdate(BaseModel):
    """Schema for updating a file batch."""
    processed_files: Optional[int] = Field(None, ge=0)
    successful_files: Optional[int] = Field(None, ge=0)
    failed_files: Optional[int] = Field(None, ge=0)
    status: Optional[BatchStatusEnum] = None
    combined_results: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    processing_log: Optional[List[Dict[str, Any]]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = Field(None, ge=0)


class FileBatchResponse(BaseModel):
    """Schema for file batch response."""
    id: str
    user_id: int
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    status: str
    total_size_bytes: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    estimated_completion_time: Optional[datetime] = None
    progress_percentage: float
    success_rate: float
    
    class Config:
        from_attributes = True


class FileBatchDetailResponse(FileBatchResponse):
    """Detailed schema for file batch with files."""
    batch_files: List[BatchFileResponse] = []
    combined_results: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    processing_log: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


# Upload Request/Response Schemas

class FileUploadRequest(BaseModel):
    """Schema for file upload request metadata."""
    language: Optional[str] = None
    auto_analyze: bool = True


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    batch_id: str
    files: List[BatchFileResponse]
    total_files: int
    queued_count: int
    message: str = "Files uploaded successfully"


class BatchStatusResponse(BaseModel):
    """Schema for batch status query response."""
    batch_id: str
    status: str
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    progress_percentage: float
    files: List[BatchFileResponse]
    is_complete: bool
    
    class Config:
        from_attributes = True


class FileAnalysisRequest(BaseModel):
    """Schema for requesting analysis of a specific file."""
    file_id: str
    language: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class BatchAnalysisRequest(BaseModel):
    """Schema for requesting analysis of an entire batch."""
    batch_id: str
    language: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


# Validation Schemas

class FileValidationResult(BaseModel):
    """Schema for file validation result."""
    is_valid: bool
    filename: str
    file_size_bytes: int
    detected_language: Optional[str] = None
    errors: List[str] = []
    warnings: List[str] = []


class BatchValidationResult(BaseModel):
    """Schema for batch validation result."""
    is_valid: bool
    total_files: int
    valid_files: int
    invalid_files: int
    file_results: List[FileValidationResult]
    errors: List[str] = []
