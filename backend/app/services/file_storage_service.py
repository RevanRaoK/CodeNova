"""
File Storage Service for Digital Ocean Spaces integration.

This service handles file upload, download, delete, and list operations
using Digital Ocean Spaces (S3-compatible API).

Requirements covered: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import os
import uuid
import hashlib
import mimetypes
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, BinaryIO
from pathlib import Path
import json
import logging

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.file_storage import StoredFile
from app.models.users import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileUploadResult(BaseModel):
    """Result of file upload operation"""
    file_id: str
    filename: str
    file_size: int
    content_type: str
    spaces_url: str
    file_hash: str
    uploaded_at: datetime


class FileDownloadResult(BaseModel):
    """Result of file download operation"""
    file_id: str
    filename: str
    content: bytes
    content_type: str
    file_size: int


class FileListResult(BaseModel):
    """Result of file list operation"""
    files: List[Dict[str, Any]]
    total_count: int
    total_size: int


class BatchUploadResult(BaseModel):
    """Result of batch file upload operation"""
    batch_id: str
    uploaded_files: List[FileUploadResult]
    failed_files: List[Dict[str, Any]]
    total_files: int
    successful_uploads: int
    failed_uploads: int
    analysis_job_ids: List[str]  # Background job IDs for code analysis


class FileStorageError(Exception):
    """Custom exception for file storage operations"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or "STORAGE_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class FileStorageService:
    """
    Service for managing file storage operations with Digital Ocean Spaces.
    
    This service provides secure file upload, download, delete, and list operations
    with proper authentication, access control, and metadata management.
    """
    
    def __init__(self):
        """Initialize the file storage service with Digital Ocean Spaces configuration"""
        self.spaces_key = settings.DO_SPACES_KEY
        self.spaces_secret = settings.DO_SPACES_SECRET
        self.bucket_name = settings.DO_SPACES_BUCKET
        self.region = settings.DO_SPACES_REGION
        self.endpoint_url = settings.DO_SPACES_ENDPOINT
        
        # File storage settings
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        self.upload_path = settings.FILE_UPLOAD_PATH
        self.signed_url_expiration = settings.SIGNED_URL_EXPIRATION_HOURS
        
        # Allowed file extensions
        allowed_extensions = settings.ALLOWED_FILE_EXTENSIONS
        self.allowed_extensions = set(ext.strip().lower() for ext in allowed_extensions.split(','))
        
        # Initialize S3 client for Digital Ocean Spaces
        self._client = None
        self._config_validated = False
    
    def _validate_configuration(self):
        """Validate that all required configuration is present"""
        if self._config_validated:
            return
            
        required_configs = {
            'DO_SPACES_KEY': self.spaces_key,
            'DO_SPACES_SECRET': self.spaces_secret,
            'DO_SPACES_BUCKET': self.bucket_name,
            'DO_SPACES_ENDPOINT': self.endpoint_url
        }
        
        missing_configs = [key for key, value in required_configs.items() if not value]
        if missing_configs:
            print(f"Missing Digital Ocean Spaces configuration: {missing_configs}")
            print(f"Current config values: {[(k, 'SET' if v else 'NOT SET') for k, v in required_configs.items()]}")
            raise FileStorageError(
                f"Missing required configuration: {', '.join(missing_configs)}",
                error_code="CONFIG_ERROR",
                details={"missing_configs": missing_configs}
            )
        
        print("Digital Ocean Spaces configuration validated successfully")
        self._config_validated = True
    
    @property
    def client(self):
        """Lazy initialization of S3 client"""
        if self._client is None:
            try:
                config = Config(
                    region_name=self.region,
                    retries={'max_attempts': 3, 'mode': 'adaptive'},
                    max_pool_connections=50
                )
                
                self._client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.spaces_key,
                    aws_secret_access_key=self.spaces_secret,
                    config=config
                )
            except Exception as e:
                raise FileStorageError(
                    f"Failed to initialize storage client: {str(e)}",
                    error_code="CLIENT_INIT_ERROR"
                )
        return self._client
    
    def _generate_file_key(self, user_id: int, filename: str) -> str:
        """Generate a unique file key for storage"""
        file_uuid = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime('%Y/%m/%d')
        safe_filename = self._sanitize_filename(filename)
        return f"{self.upload_path}{user_id}/{timestamp}/{file_uuid}_{safe_filename}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and other issues"""
        # Remove path components and keep only the filename
        filename = os.path.basename(filename)
        # Replace potentially problematic characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        sanitized = ''.join(c if c in safe_chars else '_' for c in filename)
        # Ensure filename is not empty and has reasonable length
        if not sanitized or sanitized.startswith('.'):
            sanitized = f"file_{uuid.uuid4().hex[:8]}.bin"
        return sanitized[:255]  # Limit filename length
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        if not isinstance(file_content, bytes):
            raise FileStorageError(
                f"Cannot calculate hash for non-bytes content: {type(file_content)}",
                error_code="INVALID_CONTENT_TYPE"
            )
        return hashlib.sha256(file_content).hexdigest()
    
    def _validate_file(self, file, file_size: int = None) -> None:
        """Validate uploaded file against security and size constraints"""
        # Check file size
        if file_size and file_size > self.max_file_size:
            raise FileStorageError(
                f"File size {file_size} exceeds maximum allowed size {self.max_file_size}",
                error_code="FILE_TOO_LARGE",
                details={"file_size": file_size, "max_size": self.max_file_size}
            )
        elif hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            raise FileStorageError(
                f"File size {file.size} exceeds maximum allowed size {self.max_file_size}",
                error_code="FILE_TOO_LARGE",
                details={"file_size": file.size, "max_size": self.max_file_size}
            )
        
        # Check file extension
        filename = getattr(file, 'filename', None)
        if filename:
            file_ext = Path(filename).suffix.lower().lstrip('.')
            if file_ext not in self.allowed_extensions:
                raise FileStorageError(
                    f"File extension '{file_ext}' is not allowed",
                    error_code="INVALID_FILE_TYPE",
                    details={"extension": file_ext, "allowed": list(self.allowed_extensions)}
                )
    
    async def upload_file(
        self, 
        file: UploadFile, 
        user: User, 
        db: Session,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileUploadResult:
        """
        Upload a file to Digital Ocean Spaces and store metadata in database.
        
        Args:
            file: The uploaded file
            user: The user uploading the file
            db: Database session
            metadata: Optional additional metadata
            
        Returns:
            FileUploadResult with upload details
            
        Raises:
            FileStorageError: If upload fails
        """
        try:
            # Validate configuration first
            self._validate_configuration()
            
            # Read file content first
            file_content = await file.read()
            if not isinstance(file_content, bytes):
                raise FileStorageError(
                    f"Invalid file content type: {type(file_content)}. Expected bytes.",
                    error_code="INVALID_CONTENT_TYPE"
                )
            
            file_size = len(file_content)
            print(f"DEBUG: File content type: {type(file_content)}, size: {file_size}")
            
            # Validate file with actual size
            self._validate_file(file, file_size)
            
            # Calculate file hash
            print(f"DEBUG: About to calculate hash for content type: {type(file_content)}")
            file_hash = self._calculate_file_hash(file_content)
            
            # Generate unique file key
            file_key = self._generate_file_key(user.id, file.filename)
            
            # Determine content type
            filename = getattr(file, 'filename', 'unknown')
            content_type = getattr(file, 'content_type', None) or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            # Upload to Spaces
            try:
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                    Body=file_content,
                    ContentType=content_type,
                    Metadata={
                        'user_id': str(user.id),
                        'original_filename': filename,
                        'file_hash': file_hash,
                        'upload_timestamp': datetime.utcnow().isoformat(),
                        **{str(k): str(v) for k, v in (metadata or {}).items()}
                    }
                )
            except ClientError as e:
                raise FileStorageError(
                    f"Failed to upload file to storage: {str(e)}",
                    error_code="UPLOAD_FAILED",
                    details={"aws_error": str(e)}
                )
            
            # Create database record
            file_id = str(uuid.uuid4())
            spaces_url = f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
            
            # Prepare upload metadata for storage
            upload_metadata_json = None
            if metadata:
                try:
                    upload_metadata_json = json.dumps(metadata)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Could not serialize metadata for file {filename}: {e}")
            
            stored_file = StoredFile(
                id=file_id,
                user_id=user.id,
                filename=filename,
                original_filename=filename,
                file_path=file_key,
                spaces_key=file_key,
                bucket_name=self.bucket_name,
                spaces_url=spaces_url,
                file_size=file_size,
                content_type=content_type,
                file_hash=file_hash,
                batch_id=metadata.get('batch_id') if metadata else None,
                upload_metadata=upload_metadata_json,
                processing_status="completed",
                uploaded_at=datetime.utcnow()
            )
            
            db.add(stored_file)
            db.commit()
            db.refresh(stored_file)
            
            return FileUploadResult(
                file_id=stored_file.id,
                filename=stored_file.filename,
                file_size=stored_file.file_size,
                content_type=stored_file.content_type,
                spaces_url=stored_file.spaces_url,
                file_hash=stored_file.file_hash,
                uploaded_at=stored_file.uploaded_at
            )
            
        except FileStorageError:
            raise
        except Exception as e:
            raise FileStorageError(
                f"Unexpected error during file upload: {str(e)}",
                error_code="UPLOAD_ERROR"
            )
    
    async def upload_multiple_files(
        self,
        files: List[UploadFile],
        user: User,
        db: Session,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BatchUploadResult:
        """
        Upload multiple files concurrently with proper error isolation and batch tracking.
        
        This method implements:
        - Concurrent processing of multiple files
        - Error isolation for batch operations
        - Batch tracking and metadata management
        - Background job queuing for code analysis
        
        Args:
            files: List of files to upload
            user: The user uploading the files
            db: Database session
            metadata: Optional additional metadata applied to all files
            
        Returns:
            BatchUploadResult with detailed results for each file
            
        Raises:
            FileStorageError: If batch validation fails
        """
        try:
            # Validate batch constraints
            if not files:
                raise FileStorageError(
                    "No files provided for upload",
                    error_code="NO_FILES_PROVIDED"
                )
            
            if len(files) > 10:  # Enforce batch size limit
                raise FileStorageError(
                    f"Too many files in batch. Maximum 10 files allowed, got {len(files)}",
                    error_code="BATCH_SIZE_EXCEEDED",
                    details={"file_count": len(files), "max_allowed": 10}
                )
            
            # Generate batch ID for tracking
            batch_id = str(uuid.uuid4())
            batch_metadata = metadata or {}
            batch_metadata.update({
                "batch_id": batch_id,
                "batch_upload": True,
                "total_files": len(files),
                "upload_timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Starting batch upload {batch_id} with {len(files)} files for user {user.id}")
            
            # Process files concurrently with error_isolation
            upload_tasks = []
            for i, file in enumerate(files):
                # Create file-specific metadata
                file_metadata = batch_metadata.copy()
                file_metadata.update({
                    "file_index": i,
                    "batch_position": i + 1
                })
                
                # Create upload task with error isolation
                task = self._upload_single_file_with_isolation(
                    file=file,
                    user=user,
                    db=db,
                    metadata=file_metadata,
                    file_index=i
                )
                upload_tasks.append(task)
            
            # Execute all uploads concurrently
            upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            # Process results and separate successful from failed uploads
            uploaded_files = []
            failed_files = []
            analysis_job_ids = []
            
            for i, result in enumerate(upload_results):
                if isinstance(result, Exception):
                    # Handle upload failure
                    error_info = self._extract_error_info(result, files[i])
                    failed_files.append(error_info)
                    logger.warning(f"File upload failed in batch {batch_id}: {error_info}")
                elif isinstance(result, FileUploadResult):
                    # Handle successful upload
                    uploaded_files.append(result)
                    
                    # Queue background analysis job for uploaded file
                    try:
                        job_id = await self._queue_analysis_job(result, user, batch_id)
                        if job_id:
                            analysis_job_ids.append(job_id)
                    except Exception as analysis_error:
                        logger.warning(f"Failed to queue analysis job for file {result.file_id}: {analysis_error}")
                else:
                    # Unexpected result type
                    failed_files.append({
                        "filename": files[i].filename if i < len(files) else "unknown",
                        "error_code": "UNEXPECTED_RESULT",
                        "error_message": f"Unexpected result type: {type(result)}",
                        "details": {"result_type": str(type(result))}
                    })
            
            # Create batch result
            batch_result = BatchUploadResult(
                batch_id=batch_id,
                uploaded_files=uploaded_files,
                failed_files=failed_files,
                total_files=len(files),
                successful_uploads=len(uploaded_files),
                failed_uploads=len(failed_files),
                analysis_job_ids=analysis_job_ids
            )
            
            logger.info(
                f"Batch upload {batch_id} completed: "
                f"{len(uploaded_files)} successful, {len(failed_files)} failed, "
                f"{len(analysis_job_ids)} analysis jobs queued"
            )
            
            return batch_result
            
        except FileStorageError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during batch upload: {e}")
            raise FileStorageError(
                f"Unexpected error during batch upload: {str(e)}",
                error_code="BATCH_UPLOAD_ERROR"
            )
    
    async def _upload_single_file_with_isolation(
        self,
        file: UploadFile,
        user: User,
        db: Session,
        metadata: Dict[str, Any],
        file_index: int
    ) -> FileUploadResult:
        """
        Upload a single file with error isolation for batch operations.
        
        This method wraps the single file upload to provide proper error isolation
        so that one file failure doesn't affect other files in the batch.
        """
        try:
            # Create a new database session for this file to ensure isolation
            # Note: In production, you might want to use a session factory here
            return await self.upload_file(
                file=file,
                user=user,
                db=db,
                metadata=metadata
            )
        except Exception as e:
            # Re-raise with additional context for batch processing
            raise FileStorageError(
                f"File upload failed at index {file_index}: {str(e)}",
                error_code=getattr(e, 'error_code', 'UPLOAD_ERROR'),
                details={
                    "file_index": file_index,
                    "filename": getattr(file, 'filename', 'unknown'),
                    "original_error": str(e),
                    **getattr(e, 'details', {})
                }
            )
    
    def _extract_error_info(self, error: Exception, file: UploadFile) -> Dict[str, Any]:
        """
        Extract error information from an exception for batch result reporting.
        """
        if isinstance(error, FileStorageError):
            return {
                "filename": getattr(file, 'filename', 'unknown'),
                "error_code": error.error_code,
                "error_message": error.message,
                "details": error.details
            }
        else:
            return {
                "filename": getattr(file, 'filename', 'unknown'),
                "error_code": "UNEXPECTED_ERROR",
                "error_message": str(error),
                "details": {"exception_type": type(error).__name__}
            }
    
    async def _queue_analysis_job(
        self,
        upload_result: FileUploadResult,
        user: User,
        batch_id: str
    ) -> Optional[str]:
        """
        Queue a background analysis job for an uploaded file.
        
        This method queues code analysis jobs instead of performing synchronous processing,
        improving upload performance and user experience.
        """
        try:
            # Import here to avoid circular imports
            from app.services.background_job_service import background_job_service, JobPriority
            
            # Prepare job metadata
            job_metadata = {
                "file_id": upload_result.file_id,
                "filename": upload_result.filename,
                "file_size": upload_result.file_size,
                "content_type": upload_result.content_type,
                "batch_id": batch_id,
                "upload_timestamp": upload_result.uploaded_at.isoformat()
            }
            
            # Determine job priority based on file type and size
            priority = self._determine_analysis_priority(upload_result)
            
            # Queue the analysis job
            job_id = await background_job_service.enqueue_job(
                job_name="file_code_analysis",
                args=[upload_result.file_id],
                kwargs={
                    "analysis_type": "full",
                    "batch_id": batch_id
                },
                priority=priority,
                user_id=str(user.id),
                metadata=job_metadata,
                timeout=1800,  # 30 minutes timeout for analysis
                max_retries=2
            )
            
            logger.info(f"Queued analysis job {job_id} for file {upload_result.file_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to queue analysis job for file {upload_result.file_id}: {e}")
            return None
    
    def _determine_analysis_priority(self, upload_result: FileUploadResult) -> 'JobPriority':
        """
        Determine the analysis job priority based on file characteristics.
        """
        try:
            from app.services.background_job_service import JobPriority
            
            # Priority based on file type
            code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs'}
            config_extensions = {'.json', '.yaml', '.yml', '.xml', '.toml'}
            
            file_ext = Path(upload_result.filename).suffix.lower()
            
            # High priority for code files
            if file_ext in code_extensions:
                return JobPriority.HIGH
            
            # Normal priority for config files
            if file_ext in config_extensions:
                return JobPriority.NORMAL
            
            # Low priority for other files
            return JobPriority.LOW
            
        except ImportError:
            # Fallback if background job service is not available
            return None
    
    async def download_file(
        self, 
        file_id: str, 
        user: User, 
        db: Session
    ) -> FileDownloadResult:
        """
        Download a file from Digital Ocean Spaces.
        
        Args:
            file_id: The file ID to download
            user: The user requesting the download
            db: Database session
            
        Returns:
            FileDownloadResult with file content and metadata
            
        Raises:
            FileStorageError: If download fails or access denied
        """
        try:
            # Get file record from database
            stored_file = db.query(StoredFile).filter(
                StoredFile.id == file_id,
                StoredFile.user_id == user.id  # Ensure user owns the file
            ).first()
            
            if not stored_file:
                raise FileStorageError(
                    f"File not found or access denied: {file_id}",
                    error_code="FILE_NOT_FOUND"
                )
            
            # Download from Spaces
            try:
                response = self.client.get_object(
                    Bucket=self.bucket_name,
                    Key=stored_file.spaces_key
                )
                file_content = response['Body'].read()
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    raise FileStorageError(
                        f"File not found in storage: {file_id}",
                        error_code="FILE_NOT_FOUND_STORAGE"
                    )
                else:
                    raise FileStorageError(
                        f"Failed to download file: {str(e)}",
                        error_code="DOWNLOAD_FAILED",
                        details={"aws_error": str(e)}
                    )
            
            return FileDownloadResult(
                file_id=stored_file.id,
                filename=stored_file.filename,
                content=file_content,
                content_type=stored_file.content_type,
                file_size=stored_file.file_size
            )
            
        except FileStorageError:
            raise
        except Exception as e:
            raise FileStorageError(
                f"Unexpected error during file download: {str(e)}",
                error_code="DOWNLOAD_ERROR"
            )
    
    async def delete_file(
        self, 
        file_id: str, 
        user: User, 
        db: Session
    ) -> bool:
        """
        Delete a file from both Digital Ocean Spaces and database.
        
        Args:
            file_id: The file ID to delete
            user: The user requesting the deletion
            db: Database session
            
        Returns:
            True if deletion was successful
            
        Raises:
            FileStorageError: If deletion fails or access denied
        """
        try:
            # Get file record from database
            stored_file = db.query(StoredFile).filter(
                StoredFile.id == file_id,
                StoredFile.user_id == user.id  # Ensure user owns the file
            ).first()
            
            if not stored_file:
                raise FileStorageError(
                    f"File not found or access denied: {file_id}",
                    error_code="FILE_NOT_FOUND"
                )
            
            # Delete from Spaces
            try:
                self.client.delete_object(
                    Bucket=self.bucket_name,
                    Key=stored_file.spaces_key
                )
            except ClientError as e:
                # Log warning but don't fail if file doesn't exist in storage
                if e.response['Error']['Code'] != 'NoSuchKey':
                    raise FileStorageError(
                        f"Failed to delete file from storage: {str(e)}",
                        error_code="DELETE_FAILED",
                        details={"aws_error": str(e)}
                    )
            
            # Delete from database
            db.delete(stored_file)
            db.commit()
            
            return True
            
        except FileStorageError:
            raise
        except Exception as e:
            raise FileStorageError(
                f"Unexpected error during file deletion: {str(e)}",
                error_code="DELETE_ERROR"
            )
    
    async def list_user_files(
        self, 
        user: User, 
        db: Session,
        limit: int = 50,
        offset: int = 0
    ) -> FileListResult:
        """
        List files for a specific user.
        
        Args:
            user: The user whose files to list
            db: Database session
            limit: Maximum number of files to return
            offset: Number of files to skip
            
        Returns:
            FileListResult with file list and metadata
        """
        try:
            # Query user's files from database
            query = db.query(StoredFile).filter(StoredFile.user_id == user.id)
            
            total_count = query.count()
            files_query = query.order_by(StoredFile.uploaded_at.desc()).offset(offset).limit(limit)
            stored_files = files_query.all()
            
            # Calculate total size
            from sqlalchemy import func
            total_size = db.query(func.sum(StoredFile.file_size)).filter(StoredFile.user_id == user.id).scalar() or 0
            
            # Format file list
            files = []
            for stored_file in stored_files:
                files.append({
                    'file_id': stored_file.id,
                    'filename': stored_file.filename,
                    'file_size': stored_file.file_size,
                    'content_type': stored_file.content_type,
                    'file_hash': stored_file.file_hash,
                    'uploaded_at': stored_file.uploaded_at.isoformat(),
                    'metadata': {}  # No metadata field in current model
                })
            
            return FileListResult(
                files=files,
                total_count=total_count,
                total_size=total_size
            )
            
        except Exception as e:
            raise FileStorageError(
                f"Failed to list user files: {str(e)}",
                error_code="LIST_ERROR"
            )
    
    async def generate_signed_url(
        self, 
        file_id: str, 
        user: User, 
        db: Session,
        expiration_hours: Optional[int] = None
    ) -> str:
        """
        Generate a signed URL for temporary file access.
        
        Args:
            file_id: The file ID
            user: The user requesting access
            db: Database session
            expiration_hours: URL expiration time in hours
            
        Returns:
            Signed URL string
            
        Raises:
            FileStorageError: If URL generation fails or access denied
        """
        try:
            # Get file record from database
            stored_file = db.query(StoredFile).filter(
                StoredFile.id == file_id,
                StoredFile.user_id == user.id  # Ensure user owns the file
            ).first()
            
            if not stored_file:
                raise FileStorageError(
                    f"File not found or access denied: {file_id}",
                    error_code="FILE_NOT_FOUND"
                )
            
            # Generate signed URL
            expiration = expiration_hours or self.signed_url_expiration
            expiration_seconds = expiration * 3600
            
            try:
                signed_url = self.client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': stored_file.spaces_key
                    },
                    ExpiresIn=expiration_seconds
                )
                return signed_url
                
            except ClientError as e:
                raise FileStorageError(
                    f"Failed to generate signed URL: {str(e)}",
                    error_code="SIGNED_URL_ERROR",
                    details={"aws_error": str(e)}
                )
            
        except FileStorageError:
            raise
        except Exception as e:
            raise FileStorageError(
                f"Unexpected error generating signed URL: {str(e)}",
                error_code="SIGNED_URL_ERROR"
            )
    
    async def get_file_info(
        self, 
        file_id: str, 
        user: User, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Get file information without downloading the content.
        
        Args:
            file_id: The file ID
            user: The user requesting info
            db: Database session
            
        Returns:
            Dictionary with file information
            
        Raises:
            FileStorageError: If file not found or access denied
        """
        try:
            # Get file record from database
            stored_file = db.query(StoredFile).filter(
                StoredFile.id == file_id,
                StoredFile.user_id == user.id  # Ensure user owns the file
            ).first()
            
            if not stored_file:
                raise FileStorageError(
                    f"File not found or access denied: {file_id}",
                    error_code="FILE_NOT_FOUND"
                )
            
            return {
                'file_id': stored_file.id,
                'filename': stored_file.filename,
                'file_size': stored_file.file_size,
                'content_type': stored_file.content_type,
                'file_hash': stored_file.file_hash,
                'uploaded_at': stored_file.uploaded_at.isoformat(),
                'metadata': {}  # No metadata field in current model
            }
            
        except FileStorageError:
            raise
        except Exception as e:
            raise FileStorageError(
                f"Failed to get file info: {str(e)}",
                error_code="INFO_ERROR"
            )


# Global instance
file_storage_service = FileStorageService()