"""
Background Jobs API endpoints.

This module provides REST API endpoints for:
- Job submission and queuing
- Job status tracking and monitoring
- Job progress updates
- Job result retrieval
- Queue statistics and management

Requirements covered: 2.1, 2.2, 2.3
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.background_job_service import (
    background_job_service,
    BackgroundJob,
    JobStatus,
    JobPriority,
    JobProgress
)
from app.api.deps import get_current_user
from app.schemas.users import User

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for API
class JobSubmissionRequest(BaseModel):
    """Request model for job submission."""
    job_name: str = Field(..., description="Name of the job to execute")
    args: List[Any] = Field(default_factory=list, description="Job arguments")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Job keyword arguments")
    priority: JobPriority = Field(default=JobPriority.NORMAL, description="Job priority")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional job metadata")
    delay: Optional[int] = Field(None, description="Delay in seconds before processing")
    timeout: int = Field(default=600, description="Job timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class JobResponse(BaseModel):
    """Response model for job information."""
    id: str
    name: str
    status: JobStatus
    priority: JobPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int
    max_retries: int
    timeout: int
    user_id: Optional[str] = None
    metadata: Dict[str, Any]
    
    @classmethod
    def from_background_job(cls, job: BackgroundJob) -> 'JobResponse':
        """Create response from BackgroundJob instance."""
        return cls(
            id=job.id,
            name=job.name,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            progress={
                'current_step': job.progress.current_step,
                'total_steps': job.progress.total_steps,
                'percentage': job.progress.percentage,
                'message': job.progress.message,
                'details': job.progress.details
            },
            result=job.result,
            error=job.error,
            retry_count=job.retry_count,
            max_retries=job.max_retries,
            timeout=job.timeout,
            user_id=job.user_id,
            metadata=job.metadata
        )


class JobProgressUpdate(BaseModel):
    """Model for job progress updates."""
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class QueueStatsResponse(BaseModel):
    """Response model for queue statistics."""
    timestamp: str
    total_jobs: int
    jobs_by_status: Dict[str, int]
    jobs_by_priority: Dict[str, int]
    queue_depths: Dict[str, Any]
    processing_times: Dict[str, Any]


@router.post("/submit", response_model=Dict[str, str])
async def submit_job(
    request: JobSubmissionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Submit a new background job for processing.
    
    Args:
        request: Job submission request
        current_user: Current authenticated user
        
    Returns:
        Job ID for tracking
    """
    try:
        job_id = await background_job_service.enqueue_job(
            job_name=request.job_name,
            args=request.args,
            kwargs=request.kwargs,
            priority=request.priority,
            user_id=str(current_user.id),
            metadata=request.metadata,
            delay=request.delay,
            timeout=request.timeout,
            max_retries=request.max_retries
        )
        
        logger.info(f"Job {job_id} submitted by user {current_user.id}")
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Job submitted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@router.get("/status/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the current status and details of a job.
    
    Args:
        job_id: Job ID to query
        current_user: Current authenticated user
        
    Returns:
        Job status and details
    """
    try:
        job = await background_job_service.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if user has access to this job
        if job.user_id and job.user_id != str(current_user.id):
            # Allow admin users to view any job
            if not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
        
        return JobResponse.from_background_job(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.put("/progress/{job_id}")
async def update_job_progress(
    job_id: str,
    progress_update: JobProgressUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update job progress information.
    
    Args:
        job_id: Job ID to update
        progress_update: Progress update data
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        # Check if job exists and user has access
        job = await background_job_service.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.user_id and job.user_id != str(current_user.id):
            if not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
        
        await background_job_service.update_job_progress(
            job_id=job_id,
            current_step=progress_update.current_step,
            total_steps=progress_update.total_steps,
            message=progress_update.message,
            details=progress_update.details
        )
        
        return {"message": "Job progress updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update job progress for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update job progress: {str(e)}")


@router.post("/cancel/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a queued or processing job.
    
    Args:
        job_id: Job ID to cancel
        current_user: Current authenticated user
        
    Returns:
        Cancellation result
    """
    try:
        # Check if job exists and user has access
        job = await background_job_service.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.user_id and job.user_id != str(current_user.id):
            if not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
        
        success = await background_job_service.cancel_job(job_id)
        
        if success:
            return {"message": "Job cancelled successfully"}
        else:
            return {"message": "Job could not be cancelled (may already be completed)"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/user/jobs", response_model=List[JobResponse])
async def get_user_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Get jobs for the current user.
    
    Args:
        status: Optional status filter
        limit: Maximum number of jobs to return
        current_user: Current authenticated user
        
    Returns:
        List of user's jobs
    """
    try:
        jobs = await background_job_service.get_user_jobs(
            user_id=str(current_user.id),
            status_filter=status,
            limit=limit
        )
        
        return [JobResponse.from_background_job(job) for job in jobs]
        
    except Exception as e:
        logger.error(f"Failed to get user jobs for {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user jobs: {str(e)}")


@router.get("/result/{job_id}")
async def get_job_result(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the result of a completed job.
    
    Args:
        job_id: Job ID to get result for
        current_user: Current authenticated user
        
    Returns:
        Job result data
    """
    try:
        job = await background_job_service.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check access
        if job.user_id and job.user_id != str(current_user.id):
            if not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Job is not completed")
        
        return {
            "job_id": job_id,
            "status": job.status.value,
            "result": job.result,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job result for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job result: {str(e)}")


@router.get("/queue/stats", response_model=QueueStatsResponse)
async def get_queue_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive queue statistics.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Queue statistics
    """
    try:
        # Only allow admin users to view queue statistics
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        stats = await background_job_service.get_queue_statistics()
        
        return QueueStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get queue statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue statistics: {str(e)}")


@router.post("/queue/cleanup")
async def cleanup_completed_jobs(
    older_than_hours: int = Query(24, ge=1, le=168, description="Remove jobs older than this many hours"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up completed jobs older than specified time.
    
    Args:
        older_than_hours: Remove jobs completed more than this many hours ago
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        
    Returns:
        Cleanup initiation message
    """
    try:
        # Only allow admin users to cleanup jobs
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Run cleanup in background
        background_tasks.add_task(
            background_job_service.cleanup_completed_jobs,
            older_than_hours=older_than_hours
        )
        
        return {
            "message": f"Cleanup initiated for jobs older than {older_than_hours} hours",
            "status": "started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate cleanup: {str(e)}")


# Example job submission endpoints for common tasks
@router.post("/submit/file-analysis")
async def submit_file_analysis_job(
    file_path: str,
    analysis_type: str = "full",
    priority: JobPriority = JobPriority.NORMAL,
    current_user: User = Depends(get_current_user)
):
    """
    Submit a file analysis job.
    
    Args:
        file_path: Path to the file to analyze
        analysis_type: Type of analysis to perform
        priority: Job priority
        current_user: Current authenticated user
        
    Returns:
        Job ID for tracking
    """
    try:
        job_id = await background_job_service.enqueue_job(
            job_name="file_analysis",
            args=[file_path, analysis_type],
            priority=priority,
            user_id=str(current_user.id),
            metadata={
                "file_path": file_path,
                "analysis_type": analysis_type
            }
        )
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "File analysis job submitted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit file analysis job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit file analysis job: {str(e)}")


@router.post("/submit/batch-processing")
async def submit_batch_processing_job(
    file_ids: List[str],
    priority: JobPriority = JobPriority.NORMAL,
    current_user: User = Depends(get_current_user)
):
    """
    Submit a batch file processing job.
    
    Args:
        file_ids: List of file IDs to process
        priority: Job priority
        current_user: Current authenticated user
        
    Returns:
        Job ID for tracking
    """
    try:
        if not file_ids:
            raise HTTPException(status_code=400, detail="File IDs list cannot be empty")
        
        if len(file_ids) > 100:
            raise HTTPException(status_code=400, detail="Cannot process more than 100 files at once")
        
        job_id = await background_job_service.enqueue_job(
            job_name="batch_file_processing",
            args=[file_ids],
            priority=priority,
            user_id=str(current_user.id),
            metadata={
                "file_count": len(file_ids),
                "file_ids": file_ids[:10]  # Store first 10 for reference
            }
        )
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": f"Batch processing job submitted for {len(file_ids)} files"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit batch processing job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit batch processing job: {str(e)}")