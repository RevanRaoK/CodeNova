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
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, BinaryIO
from pathlib import Path
import json

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.file_storage import StoredFile
from app.models.users import User
from app.core.config import settings


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
        self.spaces_key = os.getenv('DO_SPACES_KEY')
        self.spaces_secret = os.getenv('DO_SPACES_SECRET')
        self.bucket_name = os.getenv('DO_SPACES_BUCKET')
        self.region = os.getenv('DO_SPACES_REGION', 'nyc3')
        self.endpoint_url = os.getenv('DO_SPACES_ENDPOINT')
        
        # File storage settings
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE_MB', '50')) * 1024 * 1024  # Convert to bytes
        self.upload_path = os.getenv('FILE_UPLOAD_PATH', 'uploads/')
        self.signed_url_expiration = int(os.getenv('SIGNED_URL_EXPIRATION_HOURS', '24'))
        
        # Allowed file extensions
        allowed_extensions = os.getenv('ALLOWED_FILE_EXTENSIONS', 
                                     'pdf,doc,docx,txt,jpg,jpeg,png,gif,zip,csv,xlsx,xls,ppt,pptx')
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
            raise FileStorageError(
                f"Missing required configuration: {', '.join(missing_configs)}",
                error_code="CONFIG_ERROR",
                details={"missing_configs": missing_configs}
            )
        
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
        return hashlib.sha256(file_content).hexdigest()
    
    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file against security and size constraints"""
        # Check file size
        if hasattr(file, 'size') and file.size > self.max_file_size:
            raise FileStorageError(
                f"File size {file.size} exceeds maximum allowed size {self.max_file_size}",
                error_code="FILE_TOO_LARGE",
                details={"file_size": file.size, "max_size": self.max_file_size}
            )
        
        # Check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower().lstrip('.')
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
            
            # Validate file
            self._validate_file(file)
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Additional size check after reading
            if file_size > self.max_file_size:
                raise FileStorageError(
                    f"File size {file_size} exceeds maximum allowed size {self.max_file_size}",
                    error_code="FILE_TOO_LARGE"
                )
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_content)
            
            # Generate unique file key
            file_key = self._generate_file_key(user.id, file.filename)
            
            # Determine content type
            content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            
            # Upload to Spaces
            try:
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                    Body=file_content,
                    ContentType=content_type,
                    Metadata={
                        'user_id': str(user.id),
                        'original_filename': file.filename,
                        'file_hash': file_hash,
                        'upload_timestamp': datetime.utcnow().isoformat(),
                        **(metadata or {})
                    }
                )
            except ClientError as e:
                raise FileStorageError(
                    f"Failed to upload file to storage: {str(e)}",
                    error_code="UPLOAD_FAILED",
                    details={"aws_error": str(e)}
                )
            
            # Create database record
            stored_file = StoredFile(
                file_id=str(uuid.uuid4()),
                user_id=user.id,
                filename=file.filename,
                file_key=file_key,
                file_size=file_size,
                content_type=content_type,
                file_hash=file_hash,
                metadata=metadata or {},
                uploaded_at=datetime.utcnow()
            )
            
            db.add(stored_file)
            db.commit()
            db.refresh(stored_file)
            
            # Generate public URL
            spaces_url = f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
            
            return FileUploadResult(
                file_id=stored_file.file_id,
                filename=stored_file.filename,
                file_size=stored_file.file_size,
                content_type=stored_file.content_type,
                spaces_url=spaces_url,
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
                StoredFile.file_id == file_id,
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
                    Key=stored_file.file_key
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
                file_id=stored_file.file_id,
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
                StoredFile.file_id == file_id,
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
                    Key=stored_file.file_key
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
            total_size = db.query(StoredFile).filter(StoredFile.user_id == user.id).with_entities(
                db.func.sum(StoredFile.file_size)
            ).scalar() or 0
            
            # Format file list
            files = []
            for stored_file in stored_files:
                files.append({
                    'file_id': stored_file.file_id,
                    'filename': stored_file.filename,
                    'file_size': stored_file.file_size,
                    'content_type': stored_file.content_type,
                    'file_hash': stored_file.file_hash,
                    'uploaded_at': stored_file.uploaded_at.isoformat(),
                    'metadata': stored_file.metadata
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
                StoredFile.file_id == file_id,
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
                        'Key': stored_file.file_key
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
                StoredFile.file_id == file_id,
                StoredFile.user_id == user.id  # Ensure user owns the file
            ).first()
            
            if not stored_file:
                raise FileStorageError(
                    f"File not found or access denied: {file_id}",
                    error_code="FILE_NOT_FOUND"
                )
            
            return {
                'file_id': stored_file.file_id,
                'filename': stored_file.filename,
                'file_size': stored_file.file_size,
                'content_type': stored_file.content_type,
                'file_hash': stored_file.file_hash,
                'uploaded_at': stored_file.uploaded_at.isoformat(),
                'metadata': stored_file.metadata
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