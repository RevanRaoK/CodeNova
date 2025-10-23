"""
File validation service for multi-file upload feature.

This service provides comprehensive validation for uploaded files including:
- File type validation
- File size validation
- MIME type validation
- Content validation

Requirements covered: 12.1, 12.2
"""

import mimetypes
import magic
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel
from fastapi import UploadFile


class ValidationResult(BaseModel):
    """Result of file validation."""
    is_valid: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    warnings: List[str] = []
    file_info: Optional[Dict[str, Any]] = None


class FileValidationService:
    """
    Service for validating uploaded files.
    
    Validates file type, size, MIME type, and content to ensure
    safe and supported file uploads.
    """
    
    # Supported file extensions for code analysis
    ALLOWED_EXTENSIONS = {
        'py', 'pyw', 'pyi',  # Python
        'js', 'jsx', 'mjs', 'cjs',  # JavaScript
        'ts', 'tsx',  # TypeScript
        'java',  # Java
        'cpp', 'cc', 'cxx', 'c', 'h', 'hpp', 'hxx',  # C/C++
        'cs',  # C#
        'go',  # Go
        'rs',  # Rust
        'php',  # PHP
        'rb',  # Ruby
        'swift',  # Swift
        'kt', 'kts',  # Kotlin
        'scala',  # Scala
        'html', 'htm',  # HTML
        'css', 'scss', 'sass', 'less',  # CSS
        'sql',  # SQL
        'sh', 'bash',  # Shell
        'yaml', 'yml',  # YAML
        'json',  # JSON
        'xml',  # XML
        'md', 'markdown',  # Markdown
    }
    
    # Maximum file size in bytes (5MB)
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
    
    # Maximum file size in MB for display
    MAX_FILE_SIZE_MB = 5
    
    # Maximum number of lines in a file
    MAX_LINES = 10000
    
    # Allowed MIME types (text-based files)
    ALLOWED_MIME_PREFIXES = [
        'text/',
        'application/json',
        'application/xml',
        'application/javascript',
        'application/x-python',
        'application/x-sh',
        'application/x-yaml',
    ]
    
    # Dangerous file extensions to reject
    DANGEROUS_EXTENSIONS = {
        'exe', 'dll', 'so', 'dylib',  # Executables
        'bat', 'cmd', 'com',  # Windows scripts
        'msi', 'app',  # Installers
        'zip', 'tar', 'gz', 'rar', '7z',  # Archives
        'iso', 'img',  # Disk images
    }
    
    def __init__(self):
        """Initialize the file validation service."""
        # Initialize mimetypes
        mimetypes.init()
    
    async def validate_file(self, file: UploadFile) -> ValidationResult:
        """
        Validate an uploaded file comprehensively.
        
        Args:
            file: The uploaded file to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        warnings = []
        
        # 1. Validate filename exists
        if not file.filename:
            return ValidationResult(
                is_valid=False,
                error_message="Filename is required",
                error_code="MISSING_FILENAME"
            )
        
        # 2. Validate file extension
        extension_result = self._validate_extension(file.filename)
        if not extension_result.is_valid:
            return extension_result
        
        # 3. Check for dangerous extensions
        danger_result = self._check_dangerous_extension(file.filename)
        if not danger_result.is_valid:
            return danger_result
        
        # 4. Read file content for further validation
        try:
            content = await file.read()
            await file.seek(0)  # Reset file pointer for later use
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Failed to read file content: {str(e)}",
                error_code="READ_ERROR"
            )
        
        # 5. Validate file size
        size_result = self._validate_size(content, file.filename)
        if not size_result.is_valid:
            return size_result
        warnings.extend(size_result.warnings)
        
        # 6. Validate MIME type
        mime_result = self._validate_mime_type(content, file.filename, file.content_type)
        if not mime_result.is_valid:
            return mime_result
        warnings.extend(mime_result.warnings)
        
        # 7. Validate content (check if it's text)
        content_result = self._validate_content(content, file.filename)
        if not content_result.is_valid:
            return content_result
        warnings.extend(content_result.warnings)
        
        # 8. Validate line count
        line_result = self._validate_line_count(content, file.filename)
        if not line_result.is_valid:
            return line_result
        warnings.extend(line_result.warnings)
        
        # All validations passed
        return ValidationResult(
            is_valid=True,
            warnings=warnings,
            file_info={
                "filename": file.filename,
                "size_bytes": len(content),
                "size_kb": len(content) / 1024,
                "size_mb": len(content) / (1024 * 1024),
                "lines": len(content.decode('utf-8', errors='ignore').split('\n')),
                "extension": Path(file.filename).suffix.lower().lstrip('.'),
                "mime_type": mime_result.file_info.get("detected_mime") if mime_result.file_info else None
            }
        )
    
    def _validate_extension(self, filename: str) -> ValidationResult:
        """Validate file extension is supported."""
        path = Path(filename)
        extension = path.suffix.lower().lstrip('.')
        
        if not extension:
            return ValidationResult(
                is_valid=False,
                error_message="File must have an extension",
                error_code="NO_EXTENSION"
            )
        
        if extension not in self.ALLOWED_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                error_message=f"File type '.{extension}' is not supported. Supported types: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}",
                error_code="UNSUPPORTED_EXTENSION"
            )
        
        return ValidationResult(is_valid=True)
    
    def _check_dangerous_extension(self, filename: str) -> ValidationResult:
        """Check for dangerous file extensions."""
        path = Path(filename)
        extension = path.suffix.lower().lstrip('.')
        
        if extension in self.DANGEROUS_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                error_message=f"File type '.{extension}' is not allowed for security reasons",
                error_code="DANGEROUS_EXTENSION"
            )
        
        return ValidationResult(is_valid=True)
    
    def _validate_size(self, content: bytes, filename: str) -> ValidationResult:
        """Validate file size is within limits."""
        size_bytes = len(content)
        size_mb = size_bytes / (1024 * 1024)
        
        if size_bytes == 0:
            return ValidationResult(
                is_valid=False,
                error_message="File is empty",
                error_code="EMPTY_FILE"
            )
        
        if size_bytes > self.MAX_FILE_SIZE_BYTES:
            return ValidationResult(
                is_valid=False,
                error_message=f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({self.MAX_FILE_SIZE_MB}MB)",
                error_code="FILE_TOO_LARGE"
            )
        
        warnings = []
        if size_bytes > self.MAX_FILE_SIZE_BYTES * 0.8:  # Warn at 80% of limit
            warnings.append(f"File size ({size_mb:.2f}MB) is close to the maximum limit")
        
        return ValidationResult(is_valid=True, warnings=warnings)
    
    def _validate_mime_type(self, content: bytes, filename: str, declared_mime: Optional[str]) -> ValidationResult:
        """Validate MIME type is appropriate for code files."""
        warnings = []
        
        # Detect MIME type from content using python-magic
        try:
            detected_mime = magic.from_buffer(content, mime=True)
        except Exception:
            # Fallback to mimetypes module if python-magic fails
            detected_mime, _ = mimetypes.guess_type(filename)
            if not detected_mime:
                detected_mime = 'application/octet-stream'
        
        # Check if detected MIME type is allowed
        is_allowed = any(
            detected_mime.startswith(prefix) 
            for prefix in self.ALLOWED_MIME_PREFIXES
        )
        
        # Special case: some code files are detected as octet-stream
        if detected_mime == 'application/octet-stream':
            # Try to decode as text to verify it's a text file
            try:
                content.decode('utf-8')
                is_allowed = True
                warnings.append("File detected as binary but appears to be text")
            except UnicodeDecodeError:
                is_allowed = False
        
        if not is_allowed:
            return ValidationResult(
                is_valid=False,
                error_message=f"File MIME type '{detected_mime}' is not supported. Only text-based code files are allowed.",
                error_code="INVALID_MIME_TYPE",
                file_info={"detected_mime": detected_mime}
            )
        
        # Warn if declared MIME type doesn't match detected
        if declared_mime and declared_mime != detected_mime:
            warnings.append(f"Declared MIME type '{declared_mime}' differs from detected '{detected_mime}'")
        
        return ValidationResult(
            is_valid=True,
            warnings=warnings,
            file_info={"detected_mime": detected_mime}
        )
    
    def _validate_content(self, content: bytes, filename: str) -> ValidationResult:
        """Validate file content is valid text."""
        warnings = []
        
        # Try to decode as UTF-8
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            # Try other common encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    text_content = content.decode(encoding)
                    warnings.append(f"File decoded using {encoding} encoding instead of UTF-8")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return ValidationResult(
                    is_valid=False,
                    error_message="File content is not valid text. Only text-based code files are supported.",
                    error_code="INVALID_TEXT_CONTENT"
                )
        
        # Check for null bytes (binary content)
        if '\x00' in text_content:
            return ValidationResult(
                is_valid=False,
                error_message="File appears to contain binary content",
                error_code="BINARY_CONTENT"
            )
        
        # Check if file is completely empty or only whitespace
        if not text_content.strip():
            return ValidationResult(
                is_valid=False,
                error_message="File contains only whitespace",
                error_code="EMPTY_CONTENT"
            )
        
        return ValidationResult(is_valid=True, warnings=warnings)
    
    def _validate_line_count(self, content: bytes, filename: str) -> ValidationResult:
        """Validate file doesn't exceed maximum line count."""
        warnings = []
        
        try:
            text_content = content.decode('utf-8', errors='ignore')
            lines = text_content.split('\n')
            line_count = len(lines)
            
            if line_count > self.MAX_LINES:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File has {line_count} lines, exceeding maximum of {self.MAX_LINES} lines",
                    error_code="TOO_MANY_LINES"
                )
            
            if line_count > self.MAX_LINES * 0.8:  # Warn at 80% of limit
                warnings.append(f"File has {line_count} lines, approaching the maximum limit")
            
        except Exception as e:
            warnings.append(f"Could not count lines: {str(e)}")
        
        return ValidationResult(is_valid=True, warnings=warnings)
    
    def validate_code_content(self, code: str, language: str) -> ValidationResult:
        """
        Validate code content for direct code analysis.
        
        Args:
            code: The code content to validate
            language: The programming language
            
        Returns:
            ValidationResult with validation status
        """
        warnings = []
        
        # Check if code is empty
        if not code or not code.strip():
            return ValidationResult(
                is_valid=False,
                error_message="Code content cannot be empty",
                error_code="EMPTY_CODE"
            )
        
        # Check code length
        code_bytes = len(code.encode('utf-8'))
        if code_bytes > self.MAX_FILE_SIZE_BYTES:
            size_mb = code_bytes / (1024 * 1024)
            return ValidationResult(
                is_valid=False,
                error_message=f"Code size ({size_mb:.2f}MB) exceeds maximum allowed size ({self.MAX_FILE_SIZE_MB}MB)",
                error_code="CODE_TOO_LARGE"
            )
        
        # Check line count
        lines = code.split('\n')
        if len(lines) > self.MAX_LINES:
            return ValidationResult(
                is_valid=False,
                error_message=f"Code has {len(lines)} lines, exceeding maximum of {self.MAX_LINES} lines",
                error_code="TOO_MANY_LINES"
            )
        
        # Validate language is supported
        supported_languages = {
            'javascript', 'typescript', 'python', 'java', 'cpp', 'c', 'csharp',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'html',
            'css', 'sql', 'json', 'yaml', 'xml', 'markdown', 'shell', 'bash'
        }
        
        if language.lower() not in supported_languages:
            return ValidationResult(
                is_valid=False,
                error_message=f"Language '{language}' is not supported",
                error_code="UNSUPPORTED_LANGUAGE"
            )
        
        return ValidationResult(
            is_valid=True,
            warnings=warnings,
            file_info={
                "size_bytes": code_bytes,
                "lines": len(lines),
                "language": language
            }
        )
