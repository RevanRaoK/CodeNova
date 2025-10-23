# app/api/v1/endpoints/files.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import tempfile
import os
import logging
from pathlib import Path
from datetime import datetime
import uuid

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.users import User
from app.models.file_batch import FileBatch, BatchFile
from app.services.ai_service import aiservice
from app.services.file_upload_service import FileUploadService
from app.workers.batch_analysis_worker import process_batch_task
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

class FileUploadResponse(BaseModel):
    upload_id: str = Field(description="Unique identifier for this upload")
    filename: str = Field(description="Original filename")
    content: str = Field(description="File content as text")
    language: str = Field(description="Detected or specified programming language")
    size_bytes: int = Field(description="File size in bytes")
    size_kb: float = Field(description="File size in kilobytes")
    lines_count: int = Field(description="Number of lines in the file")
    uploaded_at: datetime = Field(description="Upload timestamp")
    content_type: str = Field(description="MIME content type")

class FileValidationError(BaseModel):
    error_type: str = Field(description="Type of validation error")
    message: str = Field(description="Error message")
    details: Optional[dict] = Field(default=None, description="Additional error details")

# Supported file extensions with enhanced validation
SUPPORTED_EXTENSIONS = {
    # JavaScript/TypeScript
    '.js', '.jsx', '.mjs', '.cjs',
    '.ts', '.tsx', '.d.ts',
    
    # Python
    '.py', '.pyw', '.pyi',
    
    # Java/JVM languages
    '.java', '.kt', '.scala', '.groovy',
    
    # C/C++
    '.c', '.cpp', '.cc', '.cxx', '.c++', '.h', '.hpp', '.hxx',
    
    # C#/.NET
    '.cs', '.vb', '.fs',
    
    # Web technologies
    '.html', '.htm', '.xhtml',
    '.css', '.scss', '.sass', '.less',
    '.xml', '.xsl', '.xsd',
    '.json', '.jsonc', '.json5',
    
    # Other languages
    '.php', '.phtml',
    '.rb', '.rbw',
    '.go', '.mod',
    '.rs',
    '.swift',
    '.r', '.R',
    '.sql',
    '.sh', '.bash', '.zsh', '.fish',
    '.ps1', '.psm1',
    '.dockerfile',
    
    # Configuration and markup
    '.yaml', '.yml',
    '.toml',
    '.ini', '.cfg', '.conf',
    '.md', '.markdown',
    '.txt', '.text',
    '.log'
}

# File size limits
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_FILE_SIZE_KB = MAX_FILE_SIZE_BYTES / 1024
MAX_LINES = 10000  # Maximum number of lines

def detect_language_from_filename(filename: str) -> str:
    """
    Detect programming language from file extension with enhanced mapping.
    
    Requirements covered: 4.3, 4.4
    """
    if not filename:
        return 'text'
    
    # Handle multiple extensions (e.g., .d.ts, .spec.js)
    path = Path(filename.lower())
    full_suffix = ''.join(path.suffixes)
    ext = path.suffix
    
    # Enhanced language mapping with better coverage
    language_map = {
        # JavaScript variants
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.mjs': 'javascript',
        '.cjs': 'javascript',
        
        # TypeScript variants
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.d.ts': 'typescript',
        
        # Python
        '.py': 'python',
        '.pyw': 'python',
        '.pyi': 'python',
        
        # Java ecosystem
        '.java': 'java',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.groovy': 'groovy',
        
        # C/C++
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c++': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.hxx': 'cpp',
        
        # .NET languages
        '.cs': 'csharp',
        '.vb': 'vbnet',
        '.fs': 'fsharp',
        
        # Web technologies
        '.html': 'html',
        '.htm': 'html',
        '.xhtml': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        
        # Data formats
        '.json': 'json',
        '.jsonc': 'json',
        '.json5': 'json',
        '.xml': 'xml',
        '.xsl': 'xml',
        '.xsd': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        
        # Other languages
        '.php': 'php',
        '.phtml': 'php',
        '.rb': 'ruby',
        '.rbw': 'ruby',
        '.go': 'go',
        '.mod': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.r': 'r',
        '.sql': 'sql',
        
        # Shell scripts
        '.sh': 'shell',
        '.bash': 'bash',
        '.zsh': 'shell',
        '.fish': 'shell',
        '.ps1': 'powershell',
        '.psm1': 'powershell',
        
        # Configuration
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'ini',
        
        # Markup
        '.md': 'markdown',
        '.markdown': 'markdown',
        
        # Docker
        '.dockerfile': 'dockerfile',
        
        # Fallback
        '.txt': 'text',
        '.text': 'text',
        '.log': 'text'
    }
    
    # Check for full suffix first (e.g., .d.ts)
    if full_suffix in language_map:
        return language_map[full_suffix]
    
    # Check for single extension
    if ext in language_map:
        return language_map[ext]
    
    # Special cases based on filename
    filename_lower = filename.lower()
    if filename_lower in ['dockerfile', 'dockerfile.dev', 'dockerfile.prod']:
        return 'dockerfile'
    elif filename_lower in ['makefile', 'makefile.am']:
        return 'makefile'
    elif filename_lower.startswith('jenkinsfile'):
        return 'groovy'
    
    return 'text'

def validate_file_content(content: str, filename: str) -> Optional[FileValidationError]:
    """
    Validate file content for potential issues.
    
    Returns None if valid, FileValidationError if invalid.
    """
    # Check for binary content (basic heuristic)
    try:
        # Check for null bytes (common in binary files)
        if '\x00' in content:
            return FileValidationError(
                error_type="binary_content",
                message="File appears to contain binary data",
                details={"filename": filename}
            )
        
        # Check for excessive line length (potential minified files)
        lines = content.split('\n')
        max_line_length = max(len(line) for line in lines) if lines else 0
        if max_line_length > 10000:
            return FileValidationError(
                error_type="excessive_line_length",
                message=f"File contains extremely long lines (max: {max_line_length} chars)",
                details={"max_line_length": max_line_length, "filename": filename}
            )
        
        # Check for reasonable character distribution (detect potential binary)
        if len(content) > 100:
            printable_ratio = sum(1 for c in content[:1000] if c.isprintable() or c in '\n\r\t') / min(1000, len(content))
            if printable_ratio < 0.7:
                return FileValidationError(
                    error_type="low_printable_ratio",
                    message="File contains high ratio of non-printable characters",
                    details={"printable_ratio": printable_ratio, "filename": filename}
                )
        
    except Exception as e:
        return FileValidationError(
            error_type="validation_error",
            message=f"Error validating file content: {str(e)}",
            details={"filename": filename}
        )
    
    return None

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="Code file to upload"),
    language: Optional[str] = Form(None, description="Override language detection"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process code files with enhanced validation and language detection.
    
    This endpoint handles file upload, validates content, detects programming language,
    and returns structured file information for use with the Monaco editor.
    
    Requirements covered: 4.1, 4.3, 4.4
    """
    upload_id = str(uuid.uuid4())
    uploaded_at = datetime.utcnow()
    
    try:
        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )
        
        # Validate file extension
        file_path = Path(file.filename)
        file_ext = file_path.suffix.lower()
        
        if file_ext not in SUPPORTED_EXTENSIONS:
            supported_list = sorted(list(SUPPORTED_EXTENSIONS))
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "unsupported_file_type",
                    "message": f"Unsupported file type: {file_ext}",
                    "supported_extensions": supported_list,
                    "filename": file.filename
                }
            )
        
        # Read and validate file size
        content_bytes = await file.read()
        file_size_bytes = len(content_bytes)
        file_size_kb = file_size_bytes / 1024
        
        if file_size_bytes > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "file_too_large",
                    "message": f"File too large: {file_size_kb:.1f}KB. Maximum allowed: {MAX_FILE_SIZE_KB:.0f}KB",
                    "file_size_kb": file_size_kb,
                    "max_size_kb": MAX_FILE_SIZE_KB,
                    "filename": file.filename
                }
            )
        
        # Decode content with multiple encoding attempts
        file_content = None
        encoding_used = None
        
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                file_content = content_bytes.decode(encoding)
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue
        
        if file_content is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "encoding_error",
                    "message": "Unable to decode file. File must be a valid text file.",
                    "filename": file.filename,
                    "attempted_encodings": ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
                }
            )
        
        # Validate content
        content_validation = validate_file_content(file_content, file.filename)
        if content_validation:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": content_validation.error_type,
                    "message": content_validation.message,
                    "details": content_validation.details
                }
            )
        
        # Count lines and validate line count
        lines = file_content.split('\n')
        lines_count = len(lines)
        
        if lines_count > MAX_LINES:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "too_many_lines",
                    "message": f"File has too many lines: {lines_count}. Maximum allowed: {MAX_LINES}",
                    "lines_count": lines_count,
                    "max_lines": MAX_LINES,
                    "filename": file.filename
                }
            )
        
        # Detect or validate language
        if language:
            # Validate provided language
            language = language.lower().strip()
            # Basic validation - could be enhanced with a proper language list
            if not language.replace('-', '').replace('_', '').isalnum():
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_language",
                        "message": f"Invalid language specification: {language}",
                        "filename": file.filename
                    }
                )
            detected_language = language
        else:
            detected_language = detect_language_from_filename(file.filename)
        
        # Determine content type
        content_type = file.content_type or "text/plain"
        
        # Log upload for monitoring (in production, consider using proper logging)
        print(f"File uploaded by user {current_user.id}: {file.filename} ({file_size_kb:.1f}KB, {lines_count} lines, {detected_language})")
        
        return FileUploadResponse(
            upload_id=upload_id,
            filename=file.filename,
            content=file_content,
            language=detected_language,
            size_bytes=file_size_bytes,
            size_kb=round(file_size_kb, 2),
            lines_count=lines_count,
            uploaded_at=uploaded_at,
            content_type=content_type
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions with their original status codes
        raise
    except Exception as e:
        # Handle unexpected errors
        print(f"Unexpected error processing file upload for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "upload_processing_error",
                "message": "An unexpected error occurred while processing the file upload",
                "filename": file.filename if file.filename else "unknown"
            }
        )

@router.post("/upload-unified", response_model=dict)
async def upload_files_unified(
    files: list[UploadFile] = File(..., description="Code files to upload (single or multiple)"),
    auto_analyze: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Unified upload endpoint that handles both single and multiple files.
    
    For single files: Returns direct analysis results
    For multiple files: Uses batch processing with progress tracking
    
    Requirements covered: 9.3, 9.4, 9.5
    """
    from app.services.batch_processing_service import batch_processing_service
    
    try:
        logger.info(f"Processing unified upload with {len(files)} files for user {current_user.id}")
        
        if len(files) == 1:
            # Single file - use direct processing for immediate results
            file = files[0]
            
            # Validate file
            if not file.filename:
                raise HTTPException(status_code=400, detail="Filename is required")
            
            # Read and validate content
            content_bytes = await file.read()
            if len(content_bytes) == 0:
                raise HTTPException(status_code=400, detail="File is empty")
            
            # Decode content
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")
            
            # Get AI analysis
            from app.services.ai_service import AIService
            ai_service = AIService()
            analysis_result = ai_service.analyze_code(
                code=content,
                language=detect_language_from_filename(file.filename),
                filename=file.filename
            )
            
            return {
                "type": "single",
                "filename": file.filename,
                "file_size_bytes": len(content_bytes),
                "lines_count": len(content.split('\n')),
                "analysis": analysis_result,
                "message": f"Successfully analyzed {file.filename}"
            }
        
        else:
            # Multiple files - use batch processing
            batch = await batch_processing_service.create_batch(
                files=files,
                user=current_user,
                db=db,
                auto_analyze=auto_analyze
            )
            logger.info(f"Batch created and processed successfully: {batch.id}")
            
            return {
                "type": "batch",
                "batch_id": batch.id,
                "status": batch.status,
                "total_files": batch.total_files,
                "processed_files": batch.processed_files,
                "successful_files": batch.successful_files,
                "failed_files": batch.failed_files,
                "progress_percentage": batch.progress_percentage,
                "is_complete": batch.is_complete,
                "estimated_completion_time": batch.estimated_completion_time,
                "completed_at": batch.completed_at,
                "message": f"Successfully created batch with {batch.total_files} files"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload-multiple-batch", response_model=dict)
async def upload_multiple_files_batch(
    files: list[UploadFile] = File(..., description="Multiple code files to upload for batch processing"),
    auto_analyze: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files for batch processing with analysis.
    
    This endpoint creates a batch processing job that handles multiple files
    concurrently and provides progress tracking and combined results.
    
    Requirements covered: 9.3, 9.4, 9.5
    """
    from app.services.batch_processing_service import batch_processing_service
    
    try:
        logger.info(f"Processing batch upload with {len(files)} files for user {current_user.id}")
        
        # Create batch with files
        batch = await batch_processing_service.create_batch(
            files=files,
            user=current_user,
            db=db,
            auto_analyze=auto_analyze
        )
        logger.info(f"Batch created and processed successfully: {batch.id}")
        
        return {
            "batch_id": batch.id,
            "status": batch.status,
            "total_files": batch.total_files,
            "processed_files": batch.processed_files,
            "successful_files": batch.successful_files,
            "failed_files": batch.failed_files,
            "progress_percentage": batch.progress_percentage,
            "is_complete": batch.is_complete,
            "estimated_completion_time": batch.estimated_completion_time,
            "completed_at": batch.completed_at,
            "message": f"Successfully created batch with {batch.total_files} files"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@router.get("/batch/{batch_id}/status")
async def get_batch_status(
    batch_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the current status and progress of a batch processing job.
    
    Requirements covered: 9.6, 9.7
    """
    from app.services.batch_processing_service import batch_processing_service
    
    try:
        print(f"DEBUG: Getting batch status for {batch_id}")
        status = await batch_processing_service.get_batch_status(batch_id, db)
        print(f"DEBUG: Batch status: {status}")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        print(f"DEBUG: Error getting batch status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")




@router.get("/batch/{batch_id}/results")
async def get_batch_results(
    batch_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the detailed analysis results for a completed batch.
    
    Requirements covered: 9.6, 9.7
    """
    from app.services.batch_processing_service import batch_processing_service
    
    try:
        results = await batch_processing_service.get_batch_results(batch_id, db)
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch results: {str(e)}")


@router.post("/upload-multiple", response_model=list[FileUploadResponse])
async def upload_multiple_files(
    files: list[UploadFile] = File(..., description="Multiple code files to upload"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process multiple code files with enhanced validation.
    
    This endpoint handles multiple file uploads, validates content, detects programming languages,
    and returns structured file information for batch code review.
    
    Requirements covered: 4.1, 4.3, 4.4
    """
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files provided for upload"
        )
    
    if len(files) > 10:  # Limit to 10 files per request
        raise HTTPException(
            status_code=400,
            detail={
                "error": "too_many_files",
                "message": f"Too many files: {len(files)}. Maximum allowed: 10",
                "file_count": len(files),
                "max_files": 10
            }
        )
    
    results = []
    errors = []
    
    for i, file in enumerate(files):
        try:
            # Process each file individually
            upload_id = str(uuid.uuid4())
            uploaded_at = datetime.utcnow()
            
            # Validate filename
            if not file.filename:
                errors.append({
                    "file_index": i,
                    "filename": f"file_{i}",
                    "error": "missing_filename",
                    "message": "Filename is required"
                })
                continue
            
            # Validate file extension
            file_path = Path(file.filename)
            file_ext = file_path.suffix.lower()
            
            if file_ext not in SUPPORTED_EXTENSIONS:
                errors.append({
                    "file_index": i,
                    "filename": file.filename,
                    "error": "unsupported_file_type",
                    "message": f"Unsupported file type: {file_ext}"
                })
                continue
            
            # Read and validate file size
            content_bytes = await file.read()
            file_size_bytes = len(content_bytes)
            file_size_kb = file_size_bytes / 1024
            
            if file_size_bytes > MAX_FILE_SIZE_BYTES:
                errors.append({
                    "file_index": i,
                    "filename": file.filename,
                    "error": "file_too_large",
                    "message": f"File too large: {file_size_kb:.1f}KB. Maximum allowed: {MAX_FILE_SIZE_KB:.0f}KB"
                })
                continue
            
            # Decode content
            file_content = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    file_content = content_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if file_content is None:
                errors.append({
                    "file_index": i,
                    "filename": file.filename,
                    "error": "encoding_error",
                    "message": "Unable to decode file. File must be a valid text file."
                })
                continue
            
            # Validate content
            content_validation = validate_file_content(file_content, file.filename)
            if content_validation:
                errors.append({
                    "file_index": i,
                    "filename": file.filename,
                    "error": content_validation.error_type,
                    "message": content_validation.message
                })
                continue
            
            # Count lines
            lines = file_content.split('\n')
            lines_count = len(lines)
            
            if lines_count > MAX_LINES:
                errors.append({
                    "file_index": i,
                    "filename": file.filename,
                    "error": "too_many_lines",
                    "message": f"File has too many lines: {lines_count}. Maximum allowed: {MAX_LINES}"
                })
                continue
            
            # Detect language
            detected_language = detect_language_from_filename(file.filename)
            content_type = file.content_type or "text/plain"
            
            # Add successful upload to results
            results.append(FileUploadResponse(
                upload_id=upload_id,
                filename=file.filename,
                content=file_content,
                language=detected_language,
                size_bytes=file_size_bytes,
                size_kb=round(file_size_kb, 2),
                lines_count=lines_count,
                uploaded_at=uploaded_at,
                content_type=content_type
            ))
            
        except Exception as e:
            errors.append({
                "file_index": i,
                "filename": file.filename if file.filename else f"file_{i}",
                "error": "processing_error",
                "message": f"Error processing file: {str(e)}"
            })
    
    # If there are errors, include them in the response
    if errors:
        response_data = {
            "uploaded_files": results,
            "errors": errors,
            "total_files": len(files),
            "successful_uploads": len(results),
            "failed_uploads": len(errors)
        }
        
        # If all files failed, return 400
        if len(results) == 0:
            raise HTTPException(
                status_code=400,
                detail=response_data
            )
        
        # If some files succeeded, return 207 (Multi-Status)
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=207,
            content=response_data
        )
    
    return results


@router.get("/analysis/{file_id}")
async def get_file_analysis(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis details for a specific file.
    
    This endpoint returns the detailed analysis results for a file,
    including issues, metrics, and suggestions.
    """
    try:
        from app.models.file_batch import BatchFile, FileBatch
        
        print(f"DEBUG: Getting analysis for file_id: {file_id}")
        
        # Get the file with user verification
        batch_file = db.query(BatchFile).join(FileBatch).filter(
            BatchFile.id == file_id,
            FileBatch.user_id == current_user.id
        ).first()
        
        if not batch_file:
            print(f"DEBUG: File not found for file_id: {file_id}, user_id: {current_user.id}")
            raise HTTPException(status_code=404, detail="File not found")
        
        print(f"DEBUG: Found file: {batch_file.filename}, status: {batch_file.status}")
        
        # Return analysis details
        return {
            "id": batch_file.id,
            "filename": batch_file.filename,
            "language": batch_file.language,
            "status": batch_file.status,
            "created_at": batch_file.created_at.isoformat() if batch_file.created_at else None,
            "completed_at": batch_file.completed_at.isoformat() if batch_file.completed_at else None,
            "processing_time_seconds": batch_file.processing_time_seconds,
            "file_size_bytes": batch_file.file_size_bytes,
            "lines_count": batch_file.lines_count,
            "issues_count": batch_file.issues_count,
            "errors_count": batch_file.errors_count,
            "warnings_count": batch_file.warnings_count,
            "suggestions_count": batch_file.suggestions_count,
            "analysis_summary": batch_file.analysis_summary,
            "issues": batch_file.analysis_results or [],
            "metrics": batch_file.analysis_metrics or {},
            "error_message": batch_file.error_message,
            "file_content": batch_file.file_content  # Include for code display
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file analysis: {e}")
        print(f"DEBUG: Error getting file analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file analysis: {str(e)}")

@router.get("/debug/batches")
async def get_user_batches_debug(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to see all user batches"""
    try:
        from app.models.file_batch import FileBatch
        
        batches = db.query(FileBatch).filter(FileBatch.user_id == current_user.id).all()
        
        result = []
        for batch in batches:
            batch_data = {
                "id": batch.id,
                "status": batch.status,
                "total_files": batch.total_files,
                "processed_files": batch.processed_files,
                "successful_files": batch.successful_files,
                "failed_files": batch.failed_files,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
                "files": []
            }
            
            for bf in batch.batch_files:
                file_data = {
                    "filename": bf.filename,
                    "status": bf.status,
                    "language": bf.language,
                    "issues_count": bf.issues_count,
                    "errors_count": bf.errors_count,
                    "warnings_count": bf.warnings_count
                }
                batch_data["files"].append(file_data)
            
            result.append(batch_data)
        
        return {"batches": result, "total": len(result)}
        
    except Exception as e:
        print(f"DEBUG: Error getting batches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_user_files(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    status: Optional[str] = Query(None, description="Filter by analysis status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's uploaded files with pagination and filtering.
    
    This endpoint returns the user's file upload history with analysis status,
    supporting pagination and filtering by language and status.
    """
    try:
        from app.models.file_batch import FileBatch, BatchFile
        from sqlalchemy import and_, desc
        
        # Build query for user's files
        query = db.query(BatchFile).join(FileBatch).filter(
            FileBatch.user_id == current_user.id
        )
        
        # Apply filters
        if language:
            query = query.filter(BatchFile.language == language)
        if status:
            query = query.filter(BatchFile.status == status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        files = query.order_by(desc(BatchFile.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # Format response
        files_data = []
        for file in files:
            files_data.append({
                "id": file.id,
                "filename": file.filename,
                "original_filename": file.original_filename,
                "language": file.language,
                "status": file.status,
                "created_at": file.created_at.isoformat() if file.created_at else None,
                "analyzed_at": file.completed_at.isoformat() if file.completed_at else None,
                "file_size_bytes": file.file_size_bytes,
                "lines_count": file.lines_count,
                "issues_count": file.issues_count or 0,
                "errors_count": file.errors_count or 0,
                "warnings_count": file.warnings_count or 0,
                "processing_time": file.processing_time_seconds
            })
        
        return {
            "files": files_data,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "has_next": (page * page_size) < total_count,
            "has_previous": page > 1
        }
        
    except Exception as e:
        logger.error(f"Failed to get user files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user files: {str(e)}")

@router.post("/code-review")
async def code_review_files(
    files: list[UploadFile] = File(..., description="Code files to review"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files and perform code review analysis.
    
    This endpoint combines file upload with immediate code analysis,
    providing a complete code review workflow for multiple files.
    
    Requirements covered: 1.1, 1.2, 4.1, 4.3, 4.4
    """
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files provided for code review"
        )
    
    if len(files) > 10:  # Limit to 10 files per request
        raise HTTPException(
            status_code=400,
            detail={
                "error": "too_many_files",
                "message": f"Too many files: {len(files)}. Maximum allowed: 10",
                "file_count": len(files),
                "max_files": 10
            }
        )
    
    # First, upload and validate all files
    try:
        uploaded_files = await upload_multiple_files(files, current_user, db)
        
        # Handle the case where upload_multiple_files returns a JSONResponse with errors
        if hasattr(uploaded_files, 'status_code'):
            # This means there were some errors in upload
            return uploaded_files
        
    except HTTPException as e:
        # Re-raise upload errors
        raise e
    
    # Now perform code analysis on each successfully uploaded file
    analysis_results = []
    
    for uploaded_file in uploaded_files:
        try:
            # Create analysis request for each file
            from app.api.v1.endpoints.analysis import DirectCodeAnalysisRequest
            
            analysis_request = DirectCodeAnalysisRequest(
                code=uploaded_file.content,
                language=uploaded_file.language,
                filename=uploaded_file.filename
            )
            
            # Import and call the analysis function
            from app.api.v1.endpoints.analysis import analyze_code_direct
            
            # Perform analysis
            analysis_result = await analyze_code_direct(analysis_request, current_user, db)
            
            # Add file information to analysis result
            analysis_result["file_info"] = {
                "upload_id": uploaded_file.upload_id,
                "filename": uploaded_file.filename,
                "language": uploaded_file.language,
                "size_bytes": uploaded_file.size_bytes,
                "size_kb": uploaded_file.size_kb,
                "lines_count": uploaded_file.lines_count,
                "uploaded_at": uploaded_file.uploaded_at.isoformat()
            }
            
            analysis_results.append(analysis_result)
            
        except Exception as e:
            # If analysis fails for a file, include error information
            analysis_results.append({
                "file_info": {
                    "upload_id": uploaded_file.upload_id,
                    "filename": uploaded_file.filename,
                    "language": uploaded_file.language,
                    "size_bytes": uploaded_file.size_bytes,
                    "size_kb": uploaded_file.size_kb,
                    "lines_count": uploaded_file.lines_count,
                    "uploaded_at": uploaded_file.uploaded_at.isoformat()
                },
                "analysis_error": {
                    "error": "analysis_failed",
                    "message": f"Code analysis failed: {str(e)}"
                },
                "status": "failed"
            })
    
    # Return comprehensive results
    return {
        "total_files": len(files),
        "uploaded_files": len(uploaded_files),
        "analyzed_files": len([r for r in analysis_results if "analysis_error" not in r]),
        "failed_analyses": len([r for r in analysis_results if "analysis_error" in r]),
        "results": analysis_results,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/supported-extensions")
def get_supported_extensions():
    """
    Get list of supported file extensions and their corresponding languages.
    
    This endpoint helps frontend applications validate files before upload.
    """
    extension_language_map = {}
    
    for ext in sorted(SUPPORTED_EXTENSIONS):
        language = detect_language_from_filename(f"example{ext}")
        if language not in extension_language_map:
            extension_language_map[language] = []
        extension_language_map[language].append(ext)
    
    return {
        "supported_extensions": sorted(list(SUPPORTED_EXTENSIONS)),
        "language_mapping": extension_language_map,
        "max_file_size_kb": MAX_FILE_SIZE_KB,
        "max_lines": MAX_LINES,
        "supported_encodings": ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    }


# ============================================================================
# New Batch Upload Endpoints for Multi-File Analysis
# Requirements covered: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 13.1, 13.2
# ============================================================================

class BatchUploadResponse(BaseModel):
    """Response model for batch file upload."""
    batch_id: str = Field(description="Unique identifier for the batch")
    total_files: int = Field(description="Total number of files in the batch")
    successful_uploads: int = Field(description="Number of successfully uploaded files")
    failed_uploads: int = Field(description="Number of failed uploads")
    status: str = Field(description="Batch status")
    files: List[dict] = Field(description="List of uploaded files with their status")
    created_at: datetime = Field(description="Batch creation timestamp")
    validation_errors: Optional[List[dict]] = Field(default=None, description="Validation errors if any")


class BatchStatusResponse(BaseModel):
    """Response model for batch status."""
    batch_id: str
    status: str
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    progress_percentage: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    files: List[dict] = Field(description="List of files with their status")


class BatchFileInfo(BaseModel):
    """Information about a file in a batch."""
    file_id: str
    filename: str
    status: str
    language: Optional[str] = None
    size_bytes: int
    analysis_id: Optional[str] = None
    issues_count: Optional[int] = None
    errors_count: Optional[int] = None
    warnings_count: Optional[int] = None
    error_message: Optional[str] = None


@router.post("/upload-batch", response_model=BatchUploadResponse)
async def upload_files_batch(
    files: List[UploadFile] = File(..., description="Multiple code files to upload for batch analysis"),
    language: Optional[str] = Form(None, description="Programming language (auto-detect if not provided)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files as a batch for background analysis.
    
    This endpoint accepts multiple files, validates them, stores them,
    and queues them for background analysis. The analysis results can
    be retrieved using the batch status endpoint.
    
    Requirements covered: 1.1, 1.2, 1.3, 1.4
    """
    try:
        logger.info(f"User {current_user.id} uploading batch of {len(files)} files")
        
        # Create file upload service
        upload_service = FileUploadService(db)
        
        # Upload files and create batch
        batch = await upload_service.upload_files_batch(
            files=files,
            user_id=current_user.id,
            language=language
        )
        
        # Get uploaded files
        batch_files = upload_service.get_batch_files(batch.id, current_user.id)
        
        # Schedule background analysis
        background_tasks.add_task(process_batch_task, batch.id)
        
        logger.info(f"Batch {batch.id} created with {len(batch_files)} files, analysis scheduled")
        
        # Prepare response
        files_info = []
        for bf in batch_files:
            files_info.append({
                "file_id": bf.id,
                "filename": bf.filename,
                "status": bf.status,
                "language": bf.language,
                "size_bytes": bf.file_size_bytes,
                "size_kb": bf.file_size_kb
            })
        
        # Extract validation errors from processing log
        validation_errors = None
        if batch.processing_log:
            for log_entry in batch.processing_log:
                if log_entry.get('event') == 'validation_errors':
                    validation_errors = log_entry.get('details', [])
        
        return BatchUploadResponse(
            batch_id=batch.id,
            total_files=batch.total_files,
            successful_uploads=len(batch_files),
            failed_uploads=len(files) - len(batch_files),
            status=batch.status,
            files=files_info,
            created_at=batch.created_at,
            validation_errors=validation_errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading batch: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Batch upload failed: {str(e)}"
        )


@router.get("/batch/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status_detailed(
    batch_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed status of a file batch.
    
    Returns the current status of the batch including progress,
    file statuses, and analysis results.
    
    Requirements covered: 1.5, 13.1, 13.3
    """
    try:
        upload_service = FileUploadService(db)
        
        # Get batch
        batch = upload_service.get_batch_status(batch_id, current_user.id)
        
        if not batch:
            raise HTTPException(
                status_code=404,
                detail=f"Batch {batch_id} not found or access denied"
            )
        
        # Get batch files
        batch_files = upload_service.get_batch_files(batch_id, current_user.id)
        
        # Prepare files info
        files_info = []
        for bf in batch_files:
            files_info.append({
                "file_id": bf.id,
                "filename": bf.filename,
                "status": bf.status,
                "language": bf.language,
                "size_bytes": bf.file_size_bytes,
                "analysis_id": bf.analysis_id,
                "issues_count": bf.issues_count,
                "errors_count": bf.errors_count,
                "warnings_count": bf.warnings_count,
                "error_message": bf.error_message,
                "processing_time_seconds": bf.processing_time_seconds
            })
        
        return BatchStatusResponse(
            batch_id=batch.id,
            status=batch.status,
            total_files=batch.total_files,
            processed_files=batch.processed_files,
            successful_files=batch.successful_files,
            failed_files=batch.failed_files,
            progress_percentage=batch.progress_percentage,
            created_at=batch.created_at,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
            processing_time_seconds=batch.processing_time_seconds,
            files=files_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch status: {str(e)}"
        )


@router.get("/batches", response_model=List[dict])
async def get_user_batches(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of records to return"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all batches for the current user.
    
    Returns a paginated list of file batches with their status.
    
    Requirements covered: 1.5, 2.3
    """
    try:
        upload_service = FileUploadService(db)
        
        # Get user batches
        batches = upload_service.get_user_batches(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status
        )
        
        # Prepare response
        batches_info = []
        for batch in batches:
            batches_info.append({
                "batch_id": batch.id,
                "total_files": batch.total_files,
                "processed_files": batch.processed_files,
                "successful_files": batch.successful_files,
                "failed_files": batch.failed_files,
                "status": batch.status,
                "progress_percentage": batch.progress_percentage,
                "created_at": batch.created_at.isoformat(),
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
                "processing_time_seconds": batch.processing_time_seconds
            })
        
        return batches_info
        
    except Exception as e:
        logger.error(f"Error getting user batches: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batches: {str(e)}"
        )


@router.get("/batch/{batch_id}/files/{file_id}", response_model=dict)
async def get_batch_file_details(
    batch_id: str,
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific file in a batch.
    
    Returns file details including analysis results if available.
    
    Requirements covered: 1.5, 2.3
    """
    try:
        # Verify batch belongs to user
        upload_service = FileUploadService(db)
        batch = upload_service.get_batch_status(batch_id, current_user.id)
        
        if not batch:
            raise HTTPException(
                status_code=404,
                detail=f"Batch {batch_id} not found or access denied"
            )
        
        # Get file
        batch_file = db.query(BatchFile).filter(
            BatchFile.id == file_id,
            BatchFile.batch_id == batch_id
        ).first()
        
        if not batch_file:
            raise HTTPException(
                status_code=404,
                detail=f"File {file_id} not found in batch {batch_id}"
            )
        
        # Prepare response
        file_info = {
            "file_id": batch_file.id,
            "batch_id": batch_file.batch_id,
            "filename": batch_file.filename,
            "original_filename": batch_file.original_filename,
            "file_size_bytes": batch_file.file_size_bytes,
            "language": batch_file.language,
            "status": batch_file.status,
            "analysis_id": batch_file.analysis_id,
            "issues_count": batch_file.issues_count,
            "errors_count": batch_file.errors_count,
            "warnings_count": batch_file.warnings_count,
            "analysis_summary": batch_file.analysis_summary,
            "analysis_results": batch_file.analysis_results,
            "error_message": batch_file.error_message,
            "error_code": batch_file.error_code,
            "created_at": batch_file.created_at.isoformat(),
            "started_processing_at": batch_file.started_processing_at.isoformat() if batch_file.started_processing_at else None,
            "completed_at": batch_file.completed_at.isoformat() if batch_file.completed_at else None,
            "processing_time_seconds": batch_file.processing_time_seconds
        }
        
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch file details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file details: {str(e)}"
        )
