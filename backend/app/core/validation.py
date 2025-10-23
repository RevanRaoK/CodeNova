"""
Input validation middleware and utilities.

This module provides comprehensive input validation for file uploads, code content,
and other user inputs to ensure security and data integrity.

Requirements covered: 12.1, 12.2, 12.3, 12.4
"""

import re
import mimetypes
from typing import Tuple, List, Optional, Dict, Any
from pathlib import Path

from fastapi import UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.monitoring import get_service_logger, ServiceType
from app.core.security import SecurityConfig, InputValidator

logger = get_service_logger(ServiceType.API, "validation")


class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class FileValidationService:
    """Service for validating file uploads."""
    
    # Allowed file extensions for code files
    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
        '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.md', '.txt',
        '.sql', '.sh', '.bash', '.ps1', '.r', '.m', '.lua', '.pl', '.dart'
    }
    
    # Maximum file size (5MB for individual files)
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # Maximum batch size (10 files)
    MAX_BATCH_SIZE = 10
    
    # Blocked file extensions (security risk)
    BLOCKED_EXTENSIONS = {
        '.exe', '.dll', '.so', '.dylib', '.bat', '.cmd', '.com', '.scr',
        '.pif', '.app', '.deb', '.rpm', '.dmg', '.pkg', '.msi'
    }
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'text/plain',
        'text/x-python',
        'text/javascript',
        'application/javascript',
        'text/x-java-source',
        'text/x-c',
        'text/x-c++',
        'text/x-csharp',
        'text/x-php',
        'text/x-ruby',
        'text/x-go',
        'text/x-rust',
        'text/x-swift',
        'text/x-kotlin',
        'text/x-scala',
        'text/html',
        'text/css',
        'application/json',
        'text/xml',
        'application/xml',
        'text/yaml',
        'text/markdown',
        'text/x-sql',
        'text/x-sh',
        'application/octet-stream'  # Generic binary, will check extension
    }
    
    @classmethod
    def validate_file(cls, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate a single file upload.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate filename
            if not file.filename:
                return False, "Filename is required"
            
            # Check for path traversal attempts
            if '..' in file.filename or '/' in file.filename or '\\' in file.filename:
                logger.warning("Path traversal attempt detected", filename=file.filename)
                return False, "Invalid filename: path traversal detected"
            
            # Validate file extension
            file_ext = Path(file.filename).suffix.lower()
            
            if not file_ext:
                return False, "File must have an extension"
            
            if file_ext in cls.BLOCKED_EXTENSIONS:
                logger.warning("Blocked file extension", filename=file.filename, extension=file_ext)
                return False, f"File type {file_ext} is not allowed for security reasons"
            
            if file_ext not in cls.ALLOWED_EXTENSIONS:
                return False, f"File type {file_ext} is not supported. Allowed types: {', '.join(sorted(cls.ALLOWED_EXTENSIONS))}"
            
            # Validate MIME type
            content_type = file.content_type
            if content_type and content_type not in cls.ALLOWED_MIME_TYPES:
                # Try to guess MIME type from filename
                guessed_type, _ = mimetypes.guess_type(file.filename)
                if not guessed_type or guessed_type not in cls.ALLOWED_MIME_TYPES:
                    logger.warning("Invalid MIME type", filename=file.filename, content_type=content_type)
                    return False, f"File MIME type {content_type} is not allowed"
            
            # Validate file size (if available)
            if hasattr(file, 'size') and file.size:
                if file.size > cls.MAX_FILE_SIZE:
                    size_mb = file.size / (1024 * 1024)
                    max_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
                    return False, f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_mb}MB)"
            
            return True, None
            
        except Exception as e:
            logger.error("File validation error", error=str(e), filename=file.filename)
            return False, f"File validation error: {str(e)}"
    
    @classmethod
    async def validate_file_content(cls, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate file content by reading and checking it.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Read file content
            content = await file.read()
            
            # Reset file pointer
            await file.seek(0)
            
            # Check actual file size
            file_size = len(content)
            if file_size > cls.MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                max_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
                return False, f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_mb}MB)"
            
            # Check if file is empty
            if file_size == 0:
                return False, "File is empty"
            
            # Check for binary content (basic check)
            try:
                content.decode('utf-8')
            except UnicodeDecodeError:
                # Allow some binary files if they have allowed extensions
                file_ext = Path(file.filename).suffix.lower()
                if file_ext not in ['.json', '.xml']:
                    logger.warning("Binary content detected", filename=file.filename)
                    return False, "File appears to contain binary data. Only text files are allowed."
            
            # Check for malicious patterns
            content_str = content.decode('utf-8', errors='ignore')
            
            # Check for executable patterns
            malicious_patterns = [
                r'<script[^>]*>.*?</script>',  # Script tags
                r'eval\s*\(',  # eval() calls
                r'exec\s*\(',  # exec() calls
                r'__import__\s*\(',  # Python imports
                r'system\s*\(',  # System calls
            ]
            
            for pattern in malicious_patterns:
                if re.search(pattern, content_str, re.IGNORECASE | re.DOTALL):
                    logger.warning("Potentially malicious content detected", filename=file.filename, pattern=pattern)
                    # Don't block, just log - these might be legitimate code
            
            return True, None
            
        except Exception as e:
            logger.error("File content validation error", error=str(e), filename=file.filename)
            return False, f"File content validation error: {str(e)}"
    
    @classmethod
    def validate_batch(cls, files: List[UploadFile]) -> Tuple[bool, Optional[str]]:
        """
        Validate a batch of files.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not files:
            return False, "No files provided"
        
        if len(files) > cls.MAX_BATCH_SIZE:
            return False, f"Too many files. Maximum {cls.MAX_BATCH_SIZE} files allowed per batch"
        
        # Check for duplicate filenames
        filenames = [f.filename for f in files]
        if len(filenames) != len(set(filenames)):
            return False, "Duplicate filenames detected in batch"
        
        return True, None


class CodeValidationService:
    """Service for validating code content."""
    
    # Maximum code length (500KB)
    MAX_CODE_LENGTH = 500 * 1024
    
    # Minimum code length
    MIN_CODE_LENGTH = 10
    
    # Supported languages
    SUPPORTED_LANGUAGES = {
        'python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'csharp',
        'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'scala',
        'html', 'css', 'sql', 'shell', 'bash', 'powershell'
    }
    
    @classmethod
    def validate_code(cls, code: str, language: str, filename: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate code content.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check code length
            if not code or len(code.strip()) < cls.MIN_CODE_LENGTH:
                return False, f"Code must be at least {cls.MIN_CODE_LENGTH} characters"
            
            if len(code) > cls.MAX_CODE_LENGTH:
                size_kb = len(code) / 1024
                max_kb = cls.MAX_CODE_LENGTH / 1024
                return False, f"Code size ({size_kb:.2f}KB) exceeds maximum allowed size ({max_kb}KB)"
            
            # Validate language
            if language and language.lower() not in cls.SUPPORTED_LANGUAGES:
                return False, f"Language '{language}' is not supported. Supported languages: {', '.join(sorted(cls.SUPPORTED_LANGUAGES))}"
            
            # Validate filename if provided (only validate if it's not None)
            if filename is not None:
                if not filename.strip():
                    return False, "Filename cannot be empty"
                
                if len(filename) > 255:
                    return False, "Filename is too long (maximum 255 characters)"
                
                # Check for invalid characters
                if re.search(r'[<>:"|?*]', filename):
                    return False, "Filename contains invalid characters"
                
                # Check for path traversal
                if '..' in filename or '/' in filename or '\\' in filename:
                    return False, "Filename cannot contain path separators"
            
            return True, None
            
        except Exception as e:
            logger.error("Code validation error", error=str(e))
            return False, f"Code validation error: {str(e)}"
    
    @classmethod
    def detect_language(cls, filename: str) -> Optional[str]:
        """Detect programming language from filename extension."""
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'shell',
            '.bash': 'bash',
            '.ps1': 'powershell'
        }
        
        ext = Path(filename).suffix.lower()
        return ext_to_lang.get(ext)


class ValidationMiddleware:
    """Middleware for request validation."""
    
    @staticmethod
    async def validate_request(request: Request, call_next):
        """Validate incoming requests."""
        try:
            # Check content length
            content_length = request.headers.get('content-length')
            if content_length:
                max_size = 50 * 1024 * 1024  # 50MB for batch uploads
                if int(content_length) > max_size:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "request_too_large",
                            "message": "Request entity too large",
                            "max_size_mb": max_size / (1024 * 1024)
                        }
                    )
            
            # Process request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error("Validation middleware error", error=str(e))
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "Internal server error during validation"
                }
            )


# Validation utility functions
def validate_email(email: str) -> bool:
    """Validate email format."""
    return InputValidator.validate_email(email)


def validate_password(password: str) -> Tuple[bool, List[str]]:
    """Validate password strength."""
    return InputValidator.validate_password(password)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    return InputValidator.sanitize_filename(filename)


def validate_url(url: str) -> bool:
    """Validate URL format and safety."""
    return InputValidator.validate_url(url)
