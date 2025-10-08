# app/api/v1/endpoints/files.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import tempfile
import os
from pathlib import Path
from datetime import datetime
import uuid

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.users import User
from app.services.ai_service import aiservice
from pydantic import BaseModel, Field

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