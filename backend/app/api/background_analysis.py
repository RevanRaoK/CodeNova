"""
API endpoints for background code analysis service.

This module provides REST API endpoints for:
- Queuing code analysis jobs
- Checking analysis status and progress
- Retrieving analysis results
- Managing batch analyses
- Analysis metrics and monitoring

Requirements covered: 2.1, 2.6
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.users import User
from app.services.background_code_analysis_service import (
    background_code_analysis_service,
    AnalysisType,
    AnalysisStatus,
    AnalysisRequest,
    AnalysisResult
)
from app.services.background_job_service import JobPriority

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["background_analysis"])


# Pydantic models for API requests and responses
class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""
    content: Optional[str] = Field(None, description="Code content to analyze")
    file_id: Optional[str] = Field(None, description="File ID from database")
    file_path: Optional[str] = Field(None, description="File path for analysis")
    language: str = Field("unknown", description="Programming language")
    analysis_type: str = Field("full", description="Type of analysis (quick, full, security, etc.)")
    priority: str = Field("normal", description="Job priority (low, normal, high, urgent)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "content": "def hello_world():\n    print('Hello, World!')",
                "language": "python",
                "analysis_type": "full",
                "priority": "normal",
                "metadata": {"source": "api_request"}
            }
        }


class BatchAnalysisRequest(BaseModel):
    """Request model for batch code analysis."""
    analyses: List[CodeAnalysisRequest] = Field(..., description="List of analysis requests")
    batch_priority: str = Field("normal", description="Priority for the entire batch")

    class Config:
        schema_extra = {
            "example": {
                "analyses": [
                    {
                        "content": "def func1(): pass",
                        "language": "python",
                        "analysis_type": "quick"
                    },
                    {
                        "file_path": "/path/to/file.js",
                        "language": "javascript",
                        "analysis_type": "full"
                    }
                ],
                "batch_priority": "normal"
            }
        }


class AnalysisResponse(BaseModel):
    """Response model for analysis operations."""
    analysis_id: str
    status: str
    message: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "queued",
                "message": "Analysis queued successfully",
                "created_at": "2024-01-01T12:00:00Z",
                "estimated_completion": "2024-01-01T12:05:00Z"
            }
        }


class BatchAnalysisResponse(BaseModel):
    """Response model for batch analysis operations."""
    batch_id: str
    total_analyses: int
    queued_analyses: int
    status: str
    message: str
    created_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_123e4567-e89b-12d3-a456-426614174000",
                "total_analyses": 5,
                "queued_analyses": 5,
                "status": "queued",
                "message": "Batch analysis queued successfully",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status."""
    analysis_id: str
    status: str
    progress_percentage: float
    current_step: str
    issues_count: Optional[int] = None
    suggestions_count: Optional[int] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "progress_percentage": 100.0,
                "current_step": "Analysis completed",
                "issues_count": 3,
                "suggestions_count": 7,
                "processing_time": 45.2,
                "error": None
            }
        }


@router.post("/queue", response_model=AnalysisResponse)
async def queue_analysis(
    request: CodeAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Queue a code analysis job for background processing.
    
    Args:
        request: Analysis request parameters
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Analysis response with job ID and status
    """
    try:
        # Validate request
        if not any([request.content, request.file_id, request.file_path]):
            raise HTTPException(
                status_code=400,
                detail="Must provide either content, file_id, or file_path"
            )
        
        # Validate analysis type
        try:
            analysis_type = AnalysisType(request.analysis_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis type: {request.analysis_type}"
            )
        
        # Validate priority
        try:
            priority = JobPriority(request.priority.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority: {request.priority}"
            )
        
        # Queue analysis
        analysis_id = await background_code_analysis_service.queue_analysis(
            file_id=request.file_id,
            file_path=request.file_path,
            content=request.content,
            language=request.language,
            analysis_type=analysis_type,
            user_id=str(current_user.id),
            priority=priority,
            metadata=request.metadata
        )
        
        logger.info(f"Queued analysis {analysis_id} for user {current_user.id}")
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="queued",
            message="Analysis queued successfully",
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue analysis")


@router.post("/batch", response_model=BatchAnalysisResponse)
async def queue_batch_analysis(
    request: BatchAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Queue multiple code analyses as a batch.
    
    Args:
        request: Batch analysis request
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Batch analysis response with batch ID and status
    """
    try:
        if not request.analyses:
            raise HTTPException(
                status_code=400,
                detail="Must provide at least one analysis request"
            )
        
        if len(request.analyses) > 50:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail="Batch size cannot exceed 50 analyses"
            )
        
        # Validate batch priority
        try:
            batch_priority = JobPriority(request.batch_priority.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid batch priority: {request.batch_priority}"
            )
        
        # Convert requests to analysis request format
        analysis_requests = []
        for analysis_req in request.analyses:
            # Validate individual request
            if not any([analysis_req.content, analysis_req.file_id, analysis_req.file_path]):
                raise HTTPException(
                    status_code=400,
                    detail="Each analysis must provide either content, file_id, or file_path"
                )
            
            try:
                AnalysisType(analysis_req.analysis_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid analysis type: {analysis_req.analysis_type}"
                )
            
            analysis_requests.append({
                'file_id': analysis_req.file_id,
                'file_path': analysis_req.file_path,
                'content': analysis_req.content,
                'language': analysis_req.language,
                'analysis_type': analysis_req.analysis_type,
                'metadata': analysis_req.metadata or {}
            })
        
        # Queue batch analysis
        batch_id = await background_code_analysis_service.queue_batch_analysis(
            analysis_requests=analysis_requests,
            batch_priority=batch_priority,
            user_id=str(current_user.id)
        )
        
        logger.info(f"Queued batch analysis {batch_id} with {len(analysis_requests)} analyses for user {current_user.id}")
        
        return BatchAnalysisResponse(
            batch_id=batch_id,
            total_analyses=len(analysis_requests),
            queued_analyses=len(analysis_requests),
            status="queued",
            message="Batch analysis queued successfully",
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue batch analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue batch analysis")


@router.get("/status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status and progress of a code analysis.
    
    Args:
        analysis_id: Analysis ID to query
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Analysis status and progress information
    """
    try:
        result = await background_code_analysis_service.get_analysis_status(analysis_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Check if user has access to this analysis
        if result.request.user_id and result.request.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate progress percentage
        progress_percentage = 0.0
        current_step = "Unknown"
        
        if result.status == AnalysisStatus.PENDING:
            progress_percentage = 0.0
            current_step = "Pending"
        elif result.status == AnalysisStatus.QUEUED:
            progress_percentage = 10.0
            current_step = "Queued for processing"
        elif result.status == AnalysisStatus.ANALYZING:
            progress_percentage = 50.0
            current_step = "Analyzing code"
        elif result.status == AnalysisStatus.PROCESSING_AI:
            progress_percentage = 75.0
            current_step = "Processing AI insights"
        elif result.status == AnalysisStatus.CACHING_RESULTS:
            progress_percentage = 90.0
            current_step = "Caching results"
        elif result.status == AnalysisStatus.COMPLETED:
            progress_percentage = 100.0
            current_step = "Analysis completed"
        elif result.status == AnalysisStatus.FAILED:
            progress_percentage = 0.0
            current_step = "Analysis failed"
        elif result.status == AnalysisStatus.CANCELLED:
            progress_percentage = 0.0
            current_step = "Analysis cancelled"
        
        return AnalysisStatusResponse(
            analysis_id=analysis_id,
            status=result.status.value,
            progress_percentage=progress_percentage,
            current_step=current_step,
            issues_count=len(result.issues) if result.issues else None,
            suggestions_count=len(result.suggestions) if result.suggestions else None,
            processing_time=result.processing_time if result.processing_time else None,
            error=result.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis status for {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis status")


@router.get("/results/{analysis_id}")
async def get_analysis_results(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the complete results of a code analysis.
    
    Args:
        analysis_id: Analysis ID to query
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Complete analysis results including issues, suggestions, and metrics
    """
    try:
        result = await background_code_analysis_service.get_analysis_status(analysis_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Check if user has access to this analysis
        if result.request.user_id and result.request.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if result.status != AnalysisStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Analysis is not completed. Current status: {result.status.value}"
            )
        
        return {
            "analysis_id": analysis_id,
            "status": result.status.value,
            "request": {
                "language": result.request.language,
                "analysis_type": result.request.analysis_type.value,
                "file_path": result.request.file_path,
                "created_at": result.request.created_at.isoformat()
            },
            "results": {
                "issues": result.issues,
                "suggestions": result.suggestions,
                "ai_insights": result.ai_insights,
                "metrics": result.metrics,
                "summary": result.summary
            },
            "timing": {
                "started_at": result.started_at.isoformat() if result.started_at else None,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "processing_time": result.processing_time
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis results for {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis results")


@router.get("/batch/status/{batch_id}")
async def get_batch_status(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of a batch analysis.
    
    Args:
        batch_id: Batch ID to query
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Batch analysis status and progress
    """
    try:
        batch_status = await background_code_analysis_service.get_batch_status(batch_id)
        
        if not batch_status:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Check if user has access to this batch
        if batch_status.get('user_id') and batch_status['user_id'] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return batch_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status for {batch_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get batch status")


@router.delete("/cancel/{analysis_id}")
async def cancel_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a queued or running analysis.
    
    Args:
        analysis_id: Analysis ID to cancel
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Cancellation status
    """
    try:
        result = await background_code_analysis_service.get_analysis_status(analysis_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Check if user has access to this analysis
        if result.request.user_id and result.request.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await background_code_analysis_service.cancel_analysis(analysis_id)
        
        if success:
            return {"message": "Analysis cancelled successfully", "analysis_id": analysis_id}
        else:
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel analysis (may already be completed or failed)"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel analysis")


@router.get("/user/analyses")
async def get_user_analyses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results")
):
    """
    Get analyses for the current user.
    
    Args:
        current_user: Authenticated user
        db: Database session
        status: Optional status filter
        limit: Maximum number of results
        
    Returns:
        List of user's analyses
    """
    try:
        status_filter = None
        if status:
            try:
                status_filter = AnalysisStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        analyses = await background_code_analysis_service.get_user_analyses(
            user_id=str(current_user.id),
            status_filter=status_filter,
            limit=limit
        )
        
        # Convert to response format
        response_analyses = []
        for analysis in analyses:
            response_analyses.append({
                "analysis_id": analysis.analysis_id,
                "status": analysis.status.value,
                "language": analysis.request.language,
                "analysis_type": analysis.request.analysis_type.value,
                "file_path": analysis.request.file_path,
                "created_at": analysis.request.created_at.isoformat(),
                "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
                "processing_time": analysis.processing_time,
                "issues_count": len(analysis.issues) if analysis.issues else 0,
                "suggestions_count": len(analysis.suggestions) if analysis.suggestions else 0
            })
        
        return {
            "analyses": response_analyses,
            "total_count": len(response_analyses),
            "user_id": current_user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user analyses for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user analyses")


@router.get("/metrics")
async def get_analysis_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analysis service metrics and statistics.
    
    Args:
        current_user: Authenticated user (admin access required)
        db: Database session
        
    Returns:
        Analysis service metrics
    """
    try:
        # Check if user has admin access (implement your admin check logic)
        # For now, allow all authenticated users
        
        metrics = await background_code_analysis_service.get_analysis_metrics()
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get analysis metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis metrics")


@router.post("/test")
async def test_analysis_service(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test the analysis service with a simple code snippet.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Test analysis results
    """
    try:
        test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# This is a test function
print(fibonacci(10))
"""
        
        analysis_id = await background_code_analysis_service.queue_analysis(
            content=test_code,
            language="python",
            analysis_type=AnalysisType.QUICK,
            user_id=str(current_user.id),
            metadata={"source": "test_endpoint"}
        )
        
        return {
            "message": "Test analysis queued successfully",
            "analysis_id": analysis_id,
            "test_code": test_code
        }
        
    except Exception as e:
        logger.error(f"Failed to run test analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to run test analysis")