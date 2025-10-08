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
    """Response model for multiple file upload"""
    uploaded_files: List[FileUploadResponse] = Field(description="List of successfully uploaded files")
    failed_files: List[dict] = Field(description="List of files that failed to upload")
    total_files: int = Field(description="Total number of files processed")
    successful_uploads: int = Field(description="Number of successful uploads")
    failed_uploads: int = Field(description="Number of failed uploads")


@router.post("/upload-multiple", response_model=MultipleFileUploadResponse)
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="Multiple files to upload"),
    metadata: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files to Digital Ocean Spaces with metadata storage.
    
    Args:
        files: List of files to upload
        metadata: Optional JSON string with additional metadata (applied to all files)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        MultipleFileUploadResponse with upload results for each file
    """
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files provided for upload"
        )
    
    if len(files) > 10:  # Limit to 10 files per request
        raise HTTPException(
            status_code=400,
            detail="Too many files. Maximum 10 files per request."
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
                detail="Invalid metadata format. Must be valid JSON."
            )
    
    uploaded_files = []
    failed_files = []
    
    for i, file in enumerate(files):
        try:
            # Add file index to metadata
            current_metadata = file_metadata.copy()
            current_metadata.update({
                "batch_upload": True,
                "file_index": i,
                "total_files": len(files)
            })
            
            # Upload file using the service
            result = await file_storage_service.upload_file(
                file=file,
                user=current_user,
                db=db,
                metadata=current_metadata
            )
            
            uploaded_files.append(FileUploadResponse(
                file_id=result.file_id,
                filename=result.filename,
                file_size=result.file_size,
                content_type=result.content_type,
                spaces_url=result.spaces_url,
                file_hash=result.file_hash,
                uploaded_at=result.uploaded_at
            ))
            
        except FileStorageError as e:
            failed_files.append({
                "filename": file.filename,
                "error_code": e.error_code,
                "error_message": e.message,
                "details": e.details
            })
        except Exception as e:
            failed_files.append({
                "filename": file.filename,
                "error_code": "UNEXPECTED_ERROR",
                "error_message": str(e),
                "details": {}
            })
    
    return MultipleFileUploadResponse(
        uploaded_files=uploaded_files,
        failed_files=failed_files,
        total_files=len(files),
        successful_uploads=len(uploaded_files),
        failed_uploads=len(failed_files)
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