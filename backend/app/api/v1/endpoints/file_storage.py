"""
File Storage API endpoints for Digital Ocean Spaces integration.

This module provides secure file upload, download, delete, and list operations
with proper authentication and access control.

Requirements covered: 4.1, 4.2, 4.3, 4.4, 4.5
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
from datetime import datetime

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.users import User
from app.services.file_storage_service import file_storage_service, FileStorageError
from app.services.background_job_service import background_job_service, JobStatus
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    file_id: str = Field(description="Unique file identifier")
    filename: str = Field(description="Original filename")
    file_size: int = Field(description="File size in bytes")
    content_type: str = Field(description="MIME content type")
    spaces_url: str = Field(description="Digital Ocean Spaces URL")
    file_hash: str = Field(description="SHA-256 hash of file content")
    uploaded_at: datetime = Field(description="Upload timestamp")


class FileInfoResponse(BaseModel):
    """Response model for file information"""
    file_id: str = Field(description="Unique file identifier")
    filename: str = Field(description="Original filename")
    file_size: int = Field(description="File size in bytes")
    content_type: str = Field(description="MIME content type")
    file_hash: str = Field(description="SHA-256 hash of file content")
    uploaded_at: str = Field(description="Upload timestamp (ISO format)")
    metadata: dict = Field(description="Additional file metadata")


class FileListResponse(BaseModel):
    """Response model for file list"""
    files: List[FileInfoResponse] = Field(description="List of user files")
    total_count: int = Field(description="Total number of files")
    total_size: int = Field(description="Total size of all files in bytes")


class SignedUrlResponse(BaseModel):
    """Response model for signed URL generation"""
    signed_url: str = Field(description="Temporary signed URL for file access")
    expires_in_hours: int = Field(description="URL expiration time in hours")


class AnalysisJobStatusResponse(BaseModel):
    """Response model for analysis job status"""
    job_id: str = Field(description="Analysis job ID")
    status: JobStatus = Field(description="Current job status")
    progress: dict = Field(description="Job progress information")
    created_at: str = Field(description="Job creation timestamp")
    started_at: Optional[str] = Field(description="Job start timestamp")
    completed_at: Optional[str] = Field(description="Job completion timestamp")
    result: Optional[dict] = Field(description="Analysis result (if completed)")
    error: Optional[str] = Field(description="Error message (if failed)")
    file_id: Optional[str] = Field(description="Associated file ID")
    metadata: dict = Field(description="Additional job metadata")


class BatchAnalysisStatusResponse(BaseModel):
    """Response model for batch analysis job status"""
    batch_id: Optional[str] = Field(description="Batch ID for related jobs")
    total_jobs: int = Field(description="Total number of analysis jobs")
    jobs: List[AnalysisJobStatusResponse] = Field(description="Individual job statuses")
    summary: dict = Field(description="Status summary by job state")


class AnalysisResultResponse(BaseModel):
    """Response model for analysis results"""
    job_id: str = Field(description="Analysis job ID")
    file_id: str = Field(description="Analyzed file ID")
    analysis_type: str = Field(description="Type of analysis performed")
    result: dict = Field(description="Analysis result data")
    completed_at: str = Field(description="Analysis completion timestamp")
    metadata: dict = Field(description="Additional result metadata")


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    metadata: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file to Digital Ocean Spaces with metadata storage.
    
    Args:
        file: The file to upload
        metadata: Optional JSON string with additional metadata
        current_user: Authenticated user
        db: Database session
        
    Returns:
        FileUploadResponse with upload details
        
    Raises:
        HTTPException: If upload fails or validation errors occur
    """
    try:
        # Parse metadata if provided
        file_metadata = {}
        if metadata:
            import json
            try:
                file_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid metadata format. Must be valid JSON."
                )
        
        # Upload file using the service
        result = await file_storage_service.upload_file(
            file=file,
            user=current_user,
            db=db,
            metadata=file_metadata
        )
        
        return FileUploadResponse(
            file_id=result.file_id,
            filename=result.filename,
            file_size=result.file_size,
            content_type=result.content_type,
            spaces_url=result.spaces_url,
            file_hash=result.file_hash,
            uploaded_at=result.uploaded_at
        )
        
    except FileStorageError as e:
        raise HTTPException(
            status_code=400 if e.error_code in ["FILE_TOO_LARGE", "INVALID_FILE_TYPE"] else 500,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during file upload: {str(e)}"
        )


class MultipleFileUploadResponse(BaseModel):
    """Response model for multiple file upload with enhanced batch processing"""
    uploaded_files: List[FileUploadResponse] = Field(description="List of successfully uploaded files")
    failed_files: List[dict] = Field(description="List of files that failed to upload")
    total_files: int = Field(description="Total number of files processed")
    successful_uploads: int = Field(description="Number of successful uploads")
    failed_uploads: int = Field(description="Number of failed uploads")
    batch_id: Optional[str] = Field(description="Batch ID for tracking related uploads")
    analysis_job_ids: List[str] = Field(default=[], description="Background job IDs for code analysis")


@router.post("/upload-multiple", response_model=MultipleFileUploadResponse)
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="Multiple files to upload"),
    metadata: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files to Digital Ocean Spaces with enhanced batch processing.
    
    This endpoint now supports:
    - File count and size validation (max 10 files, configurable size limits)
    - Concurrent file processing for better performance
    - Proper error isolation for batch operations
    - Background job queuing for code analysis
    - Batch tracking and metadata management
    - Immediate response with job IDs for background analysis
    
    Args:
        files: List of files to upload (max 10 files)
        metadata: Optional JSON string with additional metadata (applied to all files)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        MultipleFileUploadResponse with detailed upload results and analysis job IDs
        
    Raises:
        HTTPException: For validation errors, file limits, or upload failures
    """
    try:
        # Validate file count
        if not files:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "NO_FILES_PROVIDED",
                    "message": "No files provided for upload",
                    "details": {"file_count": 0}
                }
            )
        
        if len(files) > 10:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "BATCH_SIZE_EXCEEDED",
                    "message": f"Too many files. Maximum 10 files allowed, got {len(files)}",
                    "details": {"file_count": len(files), "max_allowed": 10}
                }
            )
        
        # Validate individual file sizes and total batch size
        max_file_size = 50 * 1024 * 1024  # 50MB per file
        max_batch_size = 200 * 1024 * 1024  # 200MB total batch
        total_size = 0
        oversized_files = []
        
        for i, file in enumerate(files):
            # Reset file position to get accurate size
            await file.seek(0)
            file_content = await file.read()
            file_size = len(file_content)
            await file.seek(0)  # Reset for actual upload
            
            total_size += file_size
            
            if file_size > max_file_size:
                oversized_files.append({
                    "filename": file.filename,
                    "size": file_size,
                    "max_allowed": max_file_size
                })
        
        if oversized_files:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "FILE_SIZE_EXCEEDED",
                    "message": "One or more files exceed the maximum size limit",
                    "details": {
                        "oversized_files": oversized_files,
                        "max_file_size_mb": max_file_size / (1024 * 1024)
                    }
                }
            )
        
        if total_size > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "BATCH_SIZE_EXCEEDED",
                    "message": f"Total batch size exceeds limit. Got {total_size / (1024 * 1024):.1f}MB, max allowed {max_batch_size / (1024 * 1024)}MB",
                    "details": {
                        "total_size": total_size,
                        "max_batch_size": max_batch_size,
                        "file_count": len(files)
                    }
                }
            )
        
        # Parse metadata if provided
        file_metadata = {}
        if metadata:
            import json
            try:
                file_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "INVALID_METADATA",
                        "message": "Invalid metadata format. Must be valid JSON.",
                        "details": {"provided_metadata": metadata}
                    }
                )
        
        # Use enhanced batch upload service
        batch_result = await file_storage_service.upload_multiple_files(
            files=files,
            user=current_user,
            db=db,
            metadata=file_metadata
        )
        
        # Convert service result to API response format
        uploaded_files = [
            FileUploadResponse(
                file_id=result.file_id,
                filename=result.filename,
                file_size=result.file_size,
                content_type=result.content_type,
                spaces_url=result.spaces_url,
                file_hash=result.file_hash,
                uploaded_at=result.uploaded_at
            )
            for result in batch_result.uploaded_files
        ]
        
        # Log successful upload for monitoring
        logger.info(f"Multiple file upload completed for user {current_user.id}: {batch_result.successful_uploads}/{batch_result.total_files} files uploaded, batch_id: {batch_result.batch_id}")
        
        return MultipleFileUploadResponse(
            uploaded_files=uploaded_files,
            failed_files=batch_result.failed_files,
            total_files=batch_result.total_files,
            successful_uploads=batch_result.successful_uploads,
            failed_uploads=batch_result.failed_uploads,
            batch_id=batch_result.batch_id,
            analysis_job_ids=batch_result.analysis_job_ids
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except FileStorageError as e:
        # Map service errors to appropriate HTTP status codes
        status_code_mapping = {
            "NO_FILES_PROVIDED": 400,
            "BATCH_SIZE_EXCEEDED": 400,
            "INVALID_FILE_TYPE": 400,
            "FILE_TOO_LARGE": 400,
            "UPLOAD_FAILED": 500,
            "STORAGE_ERROR": 500
        }
        
        status_code = status_code_mapping.get(e.error_code, 500)
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Multiple file upload failed for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "UPLOAD_ERROR",
                "message": "Unexpected error during multiple file upload",
                "details": {"error_type": type(e).__name__, "error_message": str(e)}
            }
        )



@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download a file by ID.
    
    Args:
        file_id: The file ID to download
        current_user: Authenticated user
        db: Database session
        
    Returns:
        StreamingResponse with file content
        
    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        result = await file_storage_service.download_file(
            file_id=file_id,
            user=current_user,
            db=db
        )
        
        # Create streaming response
        file_stream = io.BytesIO(result.content)
        
        return StreamingResponse(
            io.BytesIO(result.content),
            media_type=result.content_type,
            headers={
                "Content-Disposition": f"attachment; filename={result.filename}",
                "Content-Length": str(result.file_size)
            }
        )
        
    except FileStorageError as e:
        status_code = 404 if e.error_code in ["FILE_NOT_FOUND", "FILE_NOT_FOUND_STORAGE"] else 500
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during file download: {str(e)}"
        )


@router.delete("/delete/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a file by ID.
    
    Args:
        file_id: The file ID to delete
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        success = await file_storage_service.delete_file(
            file_id=file_id,
            user=current_user,
            db=db
        )
        
        if success:
            return {"message": "File deleted successfully", "file_id": file_id}
        else:
            raise HTTPException(
                status_code=500,
                detail="File deletion failed"
            )
        
    except FileStorageError as e:
        status_code = 404 if e.error_code == "FILE_NOT_FOUND" else 500
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during file deletion: {str(e)}"
        )


@router.get("/list", response_model=FileListResponse)
async def list_files(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of files to return"),
    offset: int = Query(0, ge=0, description="Number of files to skip"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List user's files with pagination.
    
    Args:
        limit: Maximum number of files to return (1-100)
        offset: Number of files to skip for pagination
        current_user: Authenticated user
        db: Database session
        
    Returns:
        FileListResponse with file list and metadata
    """
    try:
        result = await file_storage_service.list_user_files(
            user=current_user,
            db=db,
            limit=limit,
            offset=offset
        )
        
        # Convert files to response format
        files = [
            FileInfoResponse(
                file_id=file_data['file_id'],
                filename=file_data['filename'],
                file_size=file_data['file_size'],
                content_type=file_data['content_type'],
                file_hash=file_data['file_hash'],
                uploaded_at=file_data['uploaded_at'],
                metadata=file_data['metadata']
            )
            for file_data in result.files
        ]
        
        return FileListResponse(
            files=files,
            total_count=result.total_count,
            total_size=result.total_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing files: {str(e)}"
        )


@router.get("/info/{file_id}", response_model=FileInfoResponse)
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get file information without downloading content.
    
    Args:
        file_id: The file ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        FileInfoResponse with file metadata
        
    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        file_info = await file_storage_service.get_file_info(
            file_id=file_id,
            user=current_user,
            db=db
        )
        
        return FileInfoResponse(
            file_id=file_info['file_id'],
            filename=file_info['filename'],
            file_size=file_info['file_size'],
            content_type=file_info['content_type'],
            file_hash=file_info['file_hash'],
            uploaded_at=file_info['uploaded_at'],
            metadata=file_info['metadata']
        )
        
    except FileStorageError as e:
        status_code = 404 if e.error_code == "FILE_NOT_FOUND" else 500
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting file info: {str(e)}"
        )


@router.get("/signed-url/{file_id}", response_model=SignedUrlResponse)
async def generate_signed_url(
    file_id: str,
    expiration_hours: Optional[int] = Query(None, ge=1, le=168, description="URL expiration in hours (1-168)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a signed URL for temporary file access.
    
    Args:
        file_id: The file ID
        expiration_hours: URL expiration time in hours (1-168, default: 24)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        SignedUrlResponse with temporary access URL
        
    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        signed_url = await file_storage_service.generate_signed_url(
            file_id=file_id,
            user=current_user,
            db=db,
            expiration_hours=expiration_hours
        )
        
        return SignedUrlResponse(
            signed_url=signed_url,
            expires_in_hours=expiration_hours or 24
        )
        
    except FileStorageError as e:
        status_code = 404 if e.error_code == "FILE_NOT_FOUND" else 500
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating signed URL: {str(e)}"
        )


@router.get("/storage-info")
async def get_storage_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get storage information and limits for the current user.
    
    Returns:
        Storage configuration and usage information
    """
    try:
        # Get user's file statistics
        result = await file_storage_service.list_user_files(
            user=current_user,
            db=db,
            limit=1,
            offset=0
        )
        
        return {
            "max_file_size_mb": file_storage_service.max_file_size / (1024 * 1024),
            "allowed_extensions": list(file_storage_service.allowed_extensions),
            "signed_url_expiration_hours": file_storage_service.signed_url_expiration,
            "user_stats": {
                "total_files": result.total_count,
                "total_size_bytes": result.total_size,
                "total_size_mb": round(result.total_size / (1024 * 1024), 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting storage info: {str(e)}"
        )

# Analysis Job Status Endpoints

@router.get("/analysis/job/{job_id}", response_model=AnalysisJobStatusResponse)
async def get_analysis_job_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of a specific analysis job.
    
    Args:
        job_id: The analysis job ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        AnalysisJobStatusResponse with job status and progress
        
    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        job_status = await background_job_service.get_job_status(
            job_id=job_id,
            user=current_user,
            db=db
        )
        
        return AnalysisJobStatusResponse(
            job_id=job_status.job_id,
            status=job_status.status,
            progress=job_status.progress,
            created_at=job_status.created_at.isoformat(),
            started_at=job_status.started_at.isoformat() if job_status.started_at else None,
            completed_at=job_status.completed_at.isoformat() if job_status.completed_at else None,
            result=job_status.result,
            error=job_status.error,
            file_id=job_status.file_id,
            metadata=job_status.metadata
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "JOB_NOT_FOUND",
                    "message": f"Analysis job {job_id} not found",
                    "details": {"job_id": job_id}
                }
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error getting job status: {str(e)}"
        )


@router.get("/analysis/jobs", response_model=List[AnalysisJobStatusResponse])
async def list_analysis_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    file_id: Optional[str] = Query(None, description="Filter by file ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List analysis jobs for the current user with optional filtering.
    
    Args:
        status: Optional status filter
        file_id: Optional file ID filter
        limit: Maximum number of jobs to return (1-100)
        offset: Number of jobs to skip for pagination
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of AnalysisJobStatusResponse objects
    """
    try:
        jobs = await background_job_service.list_user_jobs(
            user=current_user,
            db=db,
            status=status,
            file_id=file_id,
            limit=limit,
            offset=offset
        )
        
        return [
            AnalysisJobStatusResponse(
                job_id=job.job_id,
                status=job.status,
                progress=job.progress,
                created_at=job.created_at.isoformat(),
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                result=job.result,
                error=job.error,
                file_id=job.file_id,
                metadata=job.metadata
            )
            for job in jobs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing analysis jobs: {str(e)}"
        )


@router.get("/analysis/batch/{batch_id}", response_model=BatchAnalysisStatusResponse)
async def get_batch_analysis_status(
    batch_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of all jobs in a batch analysis.
    
    Args:
        batch_id: The batch ID from multiple file upload
        current_user: Authenticated user
        db: Database session
        
    Returns:
        BatchAnalysisStatusResponse with all job statuses and summary
        
    Raises:
        HTTPException: If batch not found or access denied
    """
    try:
        batch_status = await background_job_service.get_batch_status(
            batch_id=batch_id,
            user=current_user,
            db=db
        )
        
        jobs = [
            AnalysisJobStatusResponse(
                job_id=job.job_id,
                status=job.status,
                progress=job.progress,
                created_at=job.created_at.isoformat(),
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                result=job.result,
                error=job.error,
                file_id=job.file_id,
                metadata=job.metadata
            )
            for job in batch_status.jobs
        ]
        
        return BatchAnalysisStatusResponse(
            batch_id=batch_id,
            total_jobs=batch_status.total_jobs,
            jobs=jobs,
            summary=batch_status.summary
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "BATCH_NOT_FOUND",
                    "message": f"Batch {batch_id} not found",
                    "details": {"batch_id": batch_id}
                }
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error getting batch status: {str(e)}"
        )


@router.get("/analysis/result/{job_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the detailed analysis result for a completed job.
    
    Args:
        job_id: The analysis job ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        AnalysisResultResponse with detailed analysis results
        
    Raises:
        HTTPException: If job not found, not completed, or access denied
    """
    try:
        result = await background_job_service.get_job_result(
            job_id=job_id,
            user=current_user,
            db=db
        )
        
        return AnalysisResultResponse(
            job_id=result.job_id,
            file_id=result.file_id,
            analysis_type=result.analysis_type,
            result=result.result,
            completed_at=result.completed_at.isoformat(),
            metadata=result.metadata
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "JOB_NOT_FOUND",
                    "message": f"Analysis job {job_id} not found",
                    "details": {"job_id": job_id}
                }
            )
        elif "not completed" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "JOB_NOT_COMPLETED",
                    "message": f"Analysis job {job_id} is not yet completed",
                    "details": {"job_id": job_id}
                }
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error getting analysis result: {str(e)}"
        )


@router.delete("/analysis/job/{job_id}")
async def cancel_analysis_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a running or queued analysis job.
    
    Args:
        job_id: The analysis job ID to cancel
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success message with cancellation details
        
    Raises:
        HTTPException: If job not found, already completed, or access denied
    """
    try:
        success = await background_job_service.cancel_job(
            job_id=job_id,
            user=current_user,
            db=db
        )
        
        if success:
            return {
                "message": "Analysis job cancelled successfully",
                "job_id": job_id,
                "cancelled_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "CANCELLATION_FAILED",
                    "message": "Job could not be cancelled (may already be completed)",
                    "details": {"job_id": job_id}
                }
            )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "JOB_NOT_FOUND",
                    "message": f"Analysis job {job_id} not found",
                    "details": {"job_id": job_id}
                }
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling analysis job: {str(e)}"
        )