"""
File upload service for multi-file batch upload and analysis.

This service handles:
- Multi-file batch uploads
- File storage and tracking
- Background job queuing for analysis
- Progress tracking

Requirements covered: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.models.file_batch import FileBatch, BatchFile, BatchStatus, FileStatus
from app.services.file_validation_service import FileValidationService
from app.core.database import get_db


class FileUploadService:
    """
    Service for handling multi-file uploads and batch processing.
    
    Manages file validation, storage, and queuing for analysis.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the file upload service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.validation_service = FileValidationService()
    
    async def upload_files_batch(
        self,
        files: List[UploadFile],
        user_id: int,
        language: Optional[str] = None
    ) -> FileBatch:
        """
        Upload multiple files as a batch for analysis.
        
        Args:
            files: List of uploaded files
            user_id: ID of the user uploading files
            language: Optional language override (auto-detect if not provided)
            
        Returns:
            FileBatch object with batch information
            
        Raises:
            HTTPException: If validation fails or upload errors occur
        """
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="No files provided for upload"
            )
        
        # Validate maximum batch size
        MAX_BATCH_SIZE = 10
        if len(files) > MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files in batch. Maximum allowed: {MAX_BATCH_SIZE}"
            )
        
        # Create batch record
        batch_id = str(uuid.uuid4())
        batch = FileBatch(
            id=batch_id,
            user_id=user_id,
            total_files=len(files),
            processed_files=0,
            successful_files=0,
            failed_files=0,
            status=BatchStatus.PENDING,
            created_at=datetime.utcnow(),
            processing_log=[]
        )
        
        self.db.add(batch)
        
        # Process each file
        total_size = 0
        batch_files = []
        validation_errors = []
        
        for index, file in enumerate(files):
            try:
                # Validate file
                validation_result = await self.validation_service.validate_file(file)
                
                if not validation_result.is_valid:
                    validation_errors.append({
                        "filename": file.filename,
                        "error": validation_result.error_message,
                        "error_code": validation_result.error_code
                    })
                    continue
                
                # Read file content
                content = await file.read()
                await file.seek(0)  # Reset for potential re-reading
                
                # Decode content
                try:
                    text_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    # Try alternative encodings
                    for encoding in ['latin-1', 'cp1252']:
                        try:
                            text_content = content.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        validation_errors.append({
                            "filename": file.filename,
                            "error": "Could not decode file content",
                            "error_code": "DECODE_ERROR"
                        })
                        continue
                
                # Detect language
                detected_language = language or self._detect_language(file.filename)
                
                # Create batch file record
                batch_file = BatchFile(
                    id=str(uuid.uuid4()),
                    batch_id=batch_id,
                    filename=file.filename,
                    original_filename=file.filename,
                    file_size_bytes=len(content),
                    content_type=file.content_type,
                    language=detected_language,
                    file_index=index,
                    status=FileStatus.UPLOADED,
                    file_content=text_content,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(batch_file)
                batch_files.append(batch_file)
                total_size += len(content)
                
            except Exception as e:
                validation_errors.append({
                    "filename": file.filename,
                    "error": f"Upload failed: {str(e)}",
                    "error_code": "UPLOAD_ERROR"
                })
        
        # Check if any files were successfully uploaded
        if len(batch_files) == 0:
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "No files could be uploaded successfully",
                    "errors": validation_errors
                }
            )
        
        # Update batch with total size and file count
        batch.total_files = len(batch_files)
        batch.total_size_bytes = total_size
        batch.status = BatchStatus.PENDING
        
        # Add validation errors to processing log
        if validation_errors:
            batch.processing_log = [{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "validation_errors",
                "details": validation_errors
            }]
        
        # Commit batch and files to database
        try:
            self.db.commit()
            self.db.refresh(batch)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save batch: {str(e)}"
            )
        
        # Send immediate upload completion notification
        from app.services.notification_service import NotificationService
        notification_service = NotificationService()
        
        try:
            await notification_service.send_upload_completion_notification(
                user_id=user_id,
                batch_id=batch_id,
                uploaded_files=len(batch_files),
                total_files=len(files),
                failed_files=len(validation_errors)
            )
        except Exception as e:
            # Don't fail the upload if notification fails
            logger.warning(f"Failed to send upload notification: {e}")
        
        # Queue analysis jobs for each file (will be implemented in background worker)
        # This will be handled by the background worker service
        
        return batch
    
    def get_batch_status(self, batch_id: str, user_id: int) -> Optional[FileBatch]:
        """
        Get the status of a file batch.
        
        Args:
            batch_id: ID of the batch
            user_id: ID of the user (for authorization)
            
        Returns:
            FileBatch object or None if not found
        """
        batch = self.db.query(FileBatch).filter(
            FileBatch.id == batch_id,
            FileBatch.user_id == user_id
        ).first()
        
        return batch
    
    def get_batch_files(self, batch_id: str, user_id: int) -> List[BatchFile]:
        """
        Get all files in a batch.
        
        Args:
            batch_id: ID of the batch
            user_id: ID of the user (for authorization)
            
        Returns:
            List of BatchFile objects
        """
        # Verify batch belongs to user
        batch = self.get_batch_status(batch_id, user_id)
        if not batch:
            return []
        
        files = self.db.query(BatchFile).filter(
            BatchFile.batch_id == batch_id
        ).order_by(BatchFile.file_index).all()
        
        return files
    
    def get_user_batches(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> List[FileBatch]:
        """
        Get all batches for a user.
        
        Args:
            user_id: ID of the user
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            status: Optional status filter
            
        Returns:
            List of FileBatch objects
        """
        query = self.db.query(FileBatch).filter(FileBatch.user_id == user_id)
        
        if status:
            query = query.filter(FileBatch.status == status)
        
        batches = query.order_by(
            FileBatch.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return batches
    
    def update_batch_status(
        self,
        batch_id: str,
        status: BatchStatus,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Optional[FileBatch]:
        """
        Update the status of a batch.
        
        Args:
            batch_id: ID of the batch
            status: New status
            error_details: Optional error details
            
        Returns:
            Updated FileBatch object or None if not found
        """
        batch = self.db.query(FileBatch).filter(FileBatch.id == batch_id).first()
        
        if not batch:
            return None
        
        batch.status = status
        
        if status == BatchStatus.PROCESSING and not batch.started_at:
            batch.started_at = datetime.utcnow()
        
        if status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.PARTIAL]:
            batch.completed_at = datetime.utcnow()
            
            if batch.started_at:
                processing_time = (batch.completed_at - batch.started_at).total_seconds()
                batch.processing_time_seconds = processing_time
        
        if error_details:
            batch.error_details = error_details
        
        self.db.commit()
        self.db.refresh(batch)
        
        return batch
    
    def update_file_status(
        self,
        file_id: str,
        status: FileStatus,
        analysis_id: Optional[str] = None,
        analysis_results: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> Optional[BatchFile]:
        """
        Update the status of a batch file.
        
        Args:
            file_id: ID of the file
            status: New status
            analysis_id: Optional analysis ID
            analysis_results: Optional analysis results
            error_message: Optional error message
            error_code: Optional error code
            
        Returns:
            Updated BatchFile object or None if not found
        """
        batch_file = self.db.query(BatchFile).filter(BatchFile.id == file_id).first()
        
        if not batch_file:
            return None
        
        batch_file.status = status
        
        if status == FileStatus.ANALYZING and not batch_file.started_processing_at:
            batch_file.started_processing_at = datetime.utcnow()
        
        if status in [FileStatus.COMPLETED, FileStatus.FAILED]:
            batch_file.completed_at = datetime.utcnow()
            
            if batch_file.started_processing_at:
                processing_time = (batch_file.completed_at - batch_file.started_processing_at).total_seconds()
                batch_file.processing_time_seconds = processing_time
        
        if analysis_id:
            batch_file.analysis_id = analysis_id
        
        if analysis_results:
            batch_file.analysis_results = analysis_results
            
            # Extract metrics from results
            if 'issues' in analysis_results:
                batch_file.issues_count = len(analysis_results['issues'])
                batch_file.errors_count = sum(
                    1 for issue in analysis_results['issues']
                    if issue.get('severity') == 'error'
                )
                batch_file.warnings_count = sum(
                    1 for issue in analysis_results['issues']
                    if issue.get('severity') == 'warning'
                )
            
            if 'summary' in analysis_results:
                batch_file.analysis_summary = analysis_results['summary']
        
        if error_message:
            batch_file.error_message = error_message
        
        if error_code:
            batch_file.error_code = error_code
        
        # Update batch progress
        batch = self.db.query(FileBatch).filter(FileBatch.id == batch_file.batch_id).first()
        if batch:
            # Count completed files
            completed_files = self.db.query(BatchFile).filter(
                BatchFile.batch_id == batch_file.batch_id,
                BatchFile.status.in_([FileStatus.COMPLETED, FileStatus.FAILED])
            ).count()
            
            successful_files = self.db.query(BatchFile).filter(
                BatchFile.batch_id == batch_file.batch_id,
                BatchFile.status == FileStatus.COMPLETED
            ).count()
            
            failed_files = self.db.query(BatchFile).filter(
                BatchFile.batch_id == batch_file.batch_id,
                BatchFile.status == FileStatus.FAILED
            ).count()
            
            batch.processed_files = completed_files
            batch.successful_files = successful_files
            batch.failed_files = failed_files
            
            # Update batch status
            if completed_files == batch.total_files:
                if failed_files == 0:
                    batch.status = BatchStatus.COMPLETED
                elif successful_files == 0:
                    batch.status = BatchStatus.FAILED
                else:
                    batch.status = BatchStatus.PARTIAL
                
                batch.completed_at = datetime.utcnow()
                if batch.started_at:
                    batch.processing_time_seconds = (batch.completed_at - batch.started_at).total_seconds()
        
        self.db.commit()
        self.db.refresh(batch_file)
        
        return batch_file
    
    def _detect_language(self, filename: str) -> str:
        """
        Detect programming language from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            Detected language name
        """
        path = Path(filename)
        extension = path.suffix.lower().lstrip('.')
        
        # Language mapping
        language_map = {
            'py': 'python',
            'pyw': 'python',
            'pyi': 'python',
            'js': 'javascript',
            'jsx': 'javascript',
            'mjs': 'javascript',
            'cjs': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'cc': 'cpp',
            'cxx': 'cpp',
            'c': 'c',
            'h': 'c',
            'hpp': 'cpp',
            'hxx': 'cpp',
            'cs': 'csharp',
            'go': 'go',
            'rs': 'rust',
            'php': 'php',
            'rb': 'ruby',
            'swift': 'swift',
            'kt': 'kotlin',
            'kts': 'kotlin',
            'scala': 'scala',
            'html': 'html',
            'htm': 'html',
            'css': 'css',
            'scss': 'css',
            'sass': 'css',
            'less': 'css',
            'sql': 'sql',
            'sh': 'shell',
            'bash': 'bash',
            'yaml': 'yaml',
            'yml': 'yaml',
            'json': 'json',
            'xml': 'xml',
            'md': 'markdown',
            'markdown': 'markdown',
        }
        
        return language_map.get(extension, 'text')
