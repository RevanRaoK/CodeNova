# app/api/v1/endpoints/file_upload.py

"""
File upload endpoints for batch processing.
Requirements: 1.1, 1.5, 2.1, 2.3
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.file_batch import FileBatch, BatchFile
from app.services.file_upload_service import FileUploadService
from app.services.file_validation_service import FileValidationService
from pydantic import BaseModel, Field

router = APIRouter()


class BatchUploadResponse(BaseModel):
    batch_id: str
    total_files: int
    queued_count: int
    status: str
    created_at: datetime
    files: List[dict]


class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    total_files: int
    completed_files: int
    failed_files: int
    progress_percentage: float
    created_at: datetime
    completed_at: Optional[datetime]
    files: List[dict]


class FileListResponse(BaseModel):
    files: List[dict]
    total: int
    page: int
    page_size: int


@router.post("/upload-batch", response_model=BatchUploadResponse)
async def upload_files_batch(
    files: List[UploadFile] = File(..., description="Multiple files to upload"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files for batch processing and analysis.
    
    Requirements: 1.1 - Multi-file upload with background analysis
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 50:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum 50 files per batch, got {len(files)}"
        )
    
    try:
        file_upload_service = FileUploadService(db)
        batch = await file_upload_service.upload_files_batch(
            files=files,
            user_id=current_user.id
        )
        
        # Format response
        files_data = []
        for batch_file in batch.files:
            files_data.append({
                "file_id": batch_file.id,
                "filename": batch_file.original_filename,
                "status": batch_file.status,
                "size_bytes": batch_file.file_size,
                "language": batch_file.language
            })
        
        return BatchUploadResponse(
            batch_id=batch.id,
            total_files=batch.total_files,
            queued_count=batch.total_files - batch.completed_files - batch.failed_files,
            status=batch.status,
            created_at=batch.created_at,
            files=files_data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of a batch upload and analysis.
    
    Requirements: 13.1, 13.3 - Real-time job status updates
    """
    batch = db.query(FileBatch).filter(
        FileBatch.id == batch_id,
        FileBatch.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get all files in batch
    batch_files = db.query(BatchFile).filter(BatchFile.batch_id == batch_id).all()
    
    files_data = []
    for batch_file in batch_files:
        files_data.append({
            "file_id": batch_file.id,
            "filename": batch_file.original_filename,
            "status": batch_file.status,
            "analysis_id": batch_file.analysis_id,
            "error_message": batch_file.error_message,
            "processed_at": batch_file.processed_at.isoformat() if batch_file.processed_at else None
        })
    
    progress = 0
    if batch.total_files > 0:
        progress = ((batch.completed_files + batch.failed_files) / batch.total_files) * 100
    
    return BatchStatusResponse(
        batch_id=batch.id,
        status=batch.status,
        total_files=batch.total_files,
        completed_files=batch.completed_files,
        failed_files=batch.failed_files,
        progress_percentage=round(progress, 2),
        created_at=batch.created_at,
        completed_at=batch.completed_at,
        files=files_data
    )


@router.get("/files", response_model=FileListResponse)
async def list_user_files(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all files uploaded by the current user.
    
    Requirements: 1.4 - View analysis history with filenames
    """
    query = db.query(BatchFile).join(FileBatch).filter(
        FileBatch.user_id == current_user.id
    )
    
    if status:
        query = query.filter(BatchFile.status == status)
    
    # Get total count
    total = query.count()
    
    # Paginate
    offset = (page - 1) * page_size
    batch_files = query.order_by(BatchFile.created_at.desc()).offset(offset).limit(page_size).all()
    
    files_data = []
    for batch_file in batch_files:
        files_data.append({
            "file_id": batch_file.id,
            "batch_id": batch_file.batch_id,
            "filename": batch_file.original_filename,
            "language": batch_file.language,
            "status": batch_file.status,
            "file_size": batch_file.file_size,
            "analysis_id": batch_file.analysis_id,
            "created_at": batch_file.created_at.isoformat(),
            "processed_at": batch_file.processed_at.isoformat() if batch_file.processed_at else None
        })
    
    return FileListResponse(
        files=files_data,
        total=total,
        page=page,
        page_size=page_size
    )
