"""
Batch processing service for multi-file upload and analysis.

This service handles the coordination of multi-file uploads, batch tracking,
and integration with the hybrid queue system for background processing.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import User, FileBatch, BatchFile, BatchStatus, FileStatus
from app.services.ai_service import AIService
from app.services.file_storage_service import FileStorageService
from app.core.hybrid_queue import HybridQueue
from app.utils.file_validation import validate_file_content, detect_language_from_filename
from app.core.config import settings

logger = logging.getLogger(__name__)


class BatchProcessingService:
    """Service for handling multi-file batch processing operations."""
    
    def __init__(self):
        self.ai_service = AIService()
        self.file_storage_service = FileStorageService()
        self.hybrid_queue = HybridQueue()
        
        # Configuration
        self.max_files_per_batch = getattr(settings, 'MAX_FILES_PER_BATCH', 10)
        self.max_file_size_bytes = getattr(settings, 'MAX_FILE_SIZE_BYTES', 1024 * 1024)  # 1MB
        self.max_total_batch_size = getattr(settings, 'MAX_TOTAL_BATCH_SIZE', 10 * 1024 * 1024)  # 10MB
        self.supported_extensions = {
            '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.c', '.cpp', '.cc', '.cxx',
            '.cs', '.html', '.htm', '.css', '.json', '.xml', '.php', '.rb', '.go', 
            '.rs', '.swift', '.kt', '.scala', '.sh', '.bash'
        }
    
    async def create_batch(
        self,
        files: List[UploadFile],
        user: User,
        db: Session,
        auto_analyze: bool = True
    ) -> FileBatch:
        """
        Create a new file batch and validate all files.
        
        Args:
            files: List of uploaded files
            user: User creating the batch
            db: Database session
            auto_analyze: Whether to automatically start analysis
            
        Returns:
            FileBatch: Created batch with initial file records
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            logger.info(f"Creating batch with {len(files)} files for user {user.id}")
            
            # Validate batch constraints
            await self._validate_batch_constraints(files, user)
            
            # Calculate total size
            total_size = 0
            for file in files:
                content = await file.read()
                total_size += len(content)
                await file.seek(0)  # Reset position immediately
            
            # Create batch record
            batch = FileBatch(
                user_id=user.id,
                total_files=len(files),
                status=BatchStatus.PENDING,
                total_size_bytes=total_size,
                estimated_completion_time=datetime.utcnow() + timedelta(minutes=len(files) * 2)
            )
            
            db.add(batch)
            db.flush()  # Get the batch ID
            
            # Create batch file records
            batch_files = []
            for i, file in enumerate(files):
                # Read file content
                content_bytes = await file.read()
                await file.seek(0)  # Reset position
                
                # Decode content
                file_content = await self._decode_file_content(content_bytes, file.filename)
                
                # Validate content
                await self._validate_file_content(file_content, file.filename)
                
                # Detect language
                language = detect_language_from_filename(file.filename)
                
                # Reset file position again before upload (important!)
                await file.seek(0)
                
                # Skip Digital Ocean Spaces upload for now - store in database only
                file_storage_result = None
                logger.info(f"Storing file {file.filename} in database (Spaces upload disabled temporarily)")
                print(f"DEBUG: File {file.filename} stored in database, size: {len(content_bytes)} bytes")
                
                # Create batch file record
                batch_file = BatchFile(
                    batch_id=batch.id,
                    filename=file.filename,
                    original_filename=file.filename,
                    file_size_bytes=len(content_bytes),
                    content_type=file.content_type,
                    language=language,
                    file_index=i,
                    file_content=file_content,  # Keep as fallback
                    status=FileStatus.UPLOADED
                )
                
                # Add storage information if upload was successful
                if file_storage_result:
                    batch_file.storage_path = file_storage_result.spaces_url
                    batch_file.stored_file_id = file_storage_result.file_id
                
                batch_files.append(batch_file)
                db.add(batch_file)
            
            batch.batch_files = batch_files
            db.commit()
            
            logger.info(f"Created batch {batch.id} with {len(files)} files for user {user.id}")
            
            # Queue for processing if auto_analyze is enabled
            if auto_analyze:
                await self._queue_batch_for_processing(batch, db)
                # Refresh batch to get updated status after processing
                db.refresh(batch)
            
            return batch
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create batch: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create batch: {str(e)}")
    
    async def process_batch(self, batch_id: str, db: Session) -> FileBatch:
        """
        Process all files in a batch through the analysis pipeline.
        
        Args:
            batch_id: ID of the batch to process
            db: Database session
            
        Returns:
            FileBatch: Updated batch with processing results
        """
        try:
            # Get batch with files
            batch = db.query(FileBatch).filter(FileBatch.id == batch_id).first()
            if not batch:
                raise HTTPException(status_code=404, detail="Batch not found")
            
            # Check if batch is already processed or processing
            if batch.status != BatchStatus.PENDING:
                logger.info(f"Batch {batch_id} already processed (status: {batch.status}), returning existing batch")
                return batch
            
            # Update batch status to processing
            batch.status = BatchStatus.PROCESSING
            batch.started_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Starting batch processing for batch {batch_id}")
            
            # Process files concurrently
            processing_tasks = []
            for batch_file in batch.batch_files:
                if batch_file.status == FileStatus.UPLOADED:
                    task = self._process_single_file(batch_file, db)
                    processing_tasks.append(task)
            
            # Execute all processing tasks
            results = await asyncio.gather(*processing_tasks, return_exceptions=True)
            
            # Update batch status based on results
            successful_count = 0
            failed_count = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_count += 1
                    logger.error(f"File processing failed in batch {batch_id}: {result}")
                else:
                    successful_count += 1
            
            # Update batch final status
            batch.processed_files = len(results)
            batch.successful_files = successful_count
            batch.failed_files = failed_count
            batch.completed_at = datetime.utcnow()
            batch.processing_time_seconds = (batch.completed_at - batch.started_at).total_seconds()
            
            if failed_count == 0:
                batch.status = BatchStatus.COMPLETED
            elif successful_count == 0:
                batch.status = BatchStatus.FAILED
            else:
                batch.status = BatchStatus.PARTIAL
            
            # Generate combined results
            batch.combined_results = await self._generate_combined_results(batch)
            
            db.commit()
            
            logger.info(f"Completed batch processing for batch {batch_id}: "
                       f"{successful_count} successful, {failed_count} failed")
            
            return batch
            
        except Exception as e:
            logger.error(f"Batch processing failed for batch {batch_id}: {e}")
            # Update batch status to failed
            if 'batch' in locals():
                batch.status = BatchStatus.FAILED
                batch.completed_at = datetime.utcnow()
                batch.error_details = {"error": str(e)}
                db.commit()
            raise
    
    async def get_batch_status(self, batch_id: str, db: Session) -> Dict[str, Any]:
        """
        Get current status and progress of a batch.
        
        Args:
            batch_id: ID of the batch
            db: Database session
            
        Returns:
            Dict containing batch status and progress information
        """
        batch = db.query(FileBatch).filter(FileBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Get file statuses
        file_statuses = []
        for batch_file in batch.batch_files:
            file_status = {
                "filename": batch_file.filename,
                "status": batch_file.status,
                "file_index": batch_file.file_index,
                "issues_count": batch_file.issues_count,
                "errors_count": batch_file.errors_count,
                "warnings_count": batch_file.warnings_count,
                "processing_time_seconds": batch_file.processing_time_seconds,
                "error_message": batch_file.error_message
            }
            file_statuses.append(file_status)
        
        return {
            "batch_id": batch.id,
            "status": batch.status,
            "progress_percentage": batch.progress_percentage,
            "total_files": batch.total_files,
            "processed_files": batch.processed_files,
            "successful_files": batch.successful_files,
            "failed_files": batch.failed_files,
            "created_at": batch.created_at,
            "started_at": batch.started_at,
            "completed_at": batch.completed_at,
            "estimated_completion_time": batch.estimated_completion_time,
            "processing_time_seconds": batch.processing_time_seconds,
            "files": file_statuses
        }
    
    async def get_batch_results(self, batch_id: str, db: Session) -> Dict[str, Any]:
        """
        Get detailed analysis results for a completed batch.
        
        Args:
            batch_id: ID of the batch
            db: Database session
            
        Returns:
            Dict containing detailed analysis results
        """
        batch = db.query(FileBatch).filter(FileBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        if not batch.is_complete:
            raise HTTPException(status_code=400, detail="Batch processing not complete")
        
        # Get detailed file results
        file_results = []
        for batch_file in batch.batch_files:
            if batch_file.status == FileStatus.COMPLETED and batch_file.has_analysis_results:
                file_result = {
                    "filename": batch_file.filename,
                    "language": batch_file.language,
                    "file_size_kb": batch_file.file_size_kb,
                    "lines_count": batch_file.lines_count,
                    "issues": batch_file.analysis_results,
                    "metrics": batch_file.analysis_metrics,
                    "summary": batch_file.analysis_summary,
                    "issues_count": batch_file.issues_count,
                    "errors_count": batch_file.errors_count,
                    "warnings_count": batch_file.warnings_count,
                    "suggestions_count": batch_file.suggestions_count
                }
                file_results.append(file_result)
        
        return {
            "batch_id": batch.id,
            "status": batch.status,
            "total_files": batch.total_files,
            "successful_files": batch.successful_files,
            "files": file_results,
            "combined_results": batch.combined_results,
            "completed_at": batch.completed_at,
            "processing_time_seconds": batch.processing_time_seconds,
            "success_rate": batch.success_rate
        }
    
    async def _validate_batch_constraints(self, files: List[UploadFile], user: User) -> None:
        """Validate batch-level constraints."""
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > self.max_files_per_batch:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files: {len(files)}. Maximum allowed: {self.max_files_per_batch}"
            )
        
        # Calculate total size
        total_size = 0
        for file in files:
            content = await file.read()
            await file.seek(0)  # Reset position
            total_size += len(content)
            
            if len(content) > self.max_file_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is too large: {len(content)} bytes. "
                           f"Maximum allowed: {self.max_file_size_bytes} bytes"
                )
        
        if total_size > self.max_total_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Total batch size too large: {total_size} bytes. "
                       f"Maximum allowed: {self.max_total_batch_size} bytes"
            )
    
    async def _decode_file_content(self, content_bytes: bytes, filename: str) -> str:
        """Decode file content with multiple encoding attempts."""
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                return content_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        raise HTTPException(
            status_code=400,
            detail=f"Unable to decode file {filename}. File must be a valid text file."
        )
    
    async def _validate_file_content(self, content: str, filename: str) -> None:
        """Validate file content."""
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}"
            )
        
        # Validate content using existing validation
        validation_result = validate_file_content(content, filename)
        if validation_result:
            raise HTTPException(
                status_code=400,
                detail=f"File {filename}: {validation_result.message}"
            )
    
    async def _process_single_file(self, batch_file: BatchFile, db: Session) -> BatchFile:
        """Process a single file through the analysis pipeline."""
        try:
            batch_file.status = FileStatus.ANALYZING
            batch_file.started_processing_at = datetime.utcnow()
            db.commit()
            
            # Perform AI analysis
            analysis_result = self.ai_service.analyze_code(
                code=batch_file.file_content,
                language=batch_file.language,
                filename=batch_file.filename
            )
            
            # Process and store results
            issues = analysis_result.get('issues', [])
            metrics = analysis_result.get('metrics', {})
            
            batch_file.analysis_results = issues
            batch_file.analysis_metrics = metrics
            batch_file.analysis_summary = analysis_result.get('summary', '')
            
            # Count issues by severity
            batch_file.issues_count = len(issues)
            batch_file.errors_count = len([i for i in issues if i.get('severity') == 'error'])
            batch_file.warnings_count = len([i for i in issues if i.get('severity') == 'warning'])
            batch_file.suggestions_count = len([i for i in issues if i.get('severity') == 'info'])
            
            batch_file.status = FileStatus.COMPLETED
            batch_file.completed_at = datetime.utcnow()
            batch_file.processing_time_seconds = (
                batch_file.completed_at - batch_file.started_processing_at
            ).total_seconds()
            
            db.commit()
            
            logger.info(f"Successfully processed file {batch_file.filename} in batch {batch_file.batch_id}")
            return batch_file
            
        except Exception as e:
            batch_file.status = FileStatus.FAILED
            batch_file.error_message = str(e)
            batch_file.error_code = "ANALYSIS_FAILED"
            batch_file.completed_at = datetime.utcnow()
            
            if batch_file.started_processing_at:
                batch_file.processing_time_seconds = (
                    batch_file.completed_at - batch_file.started_processing_at
                ).total_seconds()
            
            db.commit()
            
            logger.error(f"Failed to process file {batch_file.filename}: {e}")
            raise e
    
    async def _queue_batch_for_processing(self, batch: FileBatch, db: Session) -> None:
        """Queue batch for background processing."""
        try:
            job_data = {
                "batch_id": batch.id,
                "user_id": batch.user_id,
                "total_files": batch.total_files
            }
            
            # Skip queue for now - process immediately
            logger.info(f"Processing batch {batch.id} immediately (queue disabled temporarily)")
            
            # Refresh batch status from database to check current state
            db.refresh(batch)
            
            # Check if batch is already being processed
            if batch.status == BatchStatus.PENDING:
                logger.info(f"Starting processing for batch {batch.id}")
                await self.process_batch(batch.id, db)
            else:
                logger.info(f"Batch {batch.id} status is {batch.status}, skipping processing")
            
            logger.info(f"Queued batch {batch.id} for processing")
            
        except Exception as e:
            logger.error(f"Failed to queue batch {batch.id} for processing: {e}")
            # Don't raise here - batch is created, just not queued
    
    async def _generate_combined_results(self, batch: FileBatch) -> Dict[str, Any]:
        """Generate combined analysis results for the batch."""
        total_issues = 0
        total_errors = 0
        total_warnings = 0
        total_suggestions = 0
        total_lines = 0
        
        languages = set()
        file_summaries = []
        
        for batch_file in batch.batch_files:
            if batch_file.status == FileStatus.COMPLETED:
                total_issues += batch_file.issues_count
                total_errors += batch_file.errors_count
                total_warnings += batch_file.warnings_count
                total_suggestions += batch_file.suggestions_count
                total_lines += batch_file.lines_count
                
                if batch_file.language:
                    languages.add(batch_file.language)
                
                file_summaries.append({
                    "filename": batch_file.filename,
                    "language": batch_file.language,
                    "issues_count": batch_file.issues_count,
                    "lines_count": batch_file.lines_count
                })
        
        return {
            "summary": {
                "total_files_analyzed": batch.successful_files,
                "total_issues": total_issues,
                "total_errors": total_errors,
                "total_warnings": total_warnings,
                "total_suggestions": total_suggestions,
                "total_lines_of_code": total_lines,
                "languages_detected": list(languages),
                "average_issues_per_file": total_issues / max(batch.successful_files, 1)
            },
            "file_summaries": file_summaries,
            "processing_stats": {
                "processing_time_seconds": batch.processing_time_seconds,
                "success_rate": batch.success_rate,
                "files_per_minute": (batch.successful_files / max(batch.processing_time_seconds / 60, 1)) if batch.processing_time_seconds else 0
            }
        }


# Singleton instance
batch_processing_service = BatchProcessingService()