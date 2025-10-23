"""
File validation utilities for code analysis.

This module provides validation functions for uploaded files,
content validation, and language detection.
"""

import re
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, NamedTuple


class ValidationResult(NamedTuple):
    """Result of file validation."""
    is_valid: bool
    message: Optional[str] = None
    error_code: Optional[str] = None


def validate_file_content(content: str, filename: str) -> Optional[ValidationResult]:
    """
    Validate file content for security and quality.
    
    Args:
        content: The file content to validate
        filename: Name of the file being validated
        
    Returns:
        ValidationResult if validation fails, None if valid
    """
    if not content:
        return ValidationResult(False, "File is empty", "EMPTY_FILE")
    
    # Check for binary content
    if _contains_binary_content(content):
        return ValidationResult(False, "File contains binary content", "BINARY_CONTENT")
    
    # Check file size (content length)
    max_content_length = 1024 * 1024  # 1MB in characters
    if len(content) > max_content_length:
        return ValidationResult(
            False, 
            f"File content too large: {len(content)} characters. Maximum: {max_content_length}",
            "CONTENT_TOO_LARGE"
        )
    
    # Check for potentially malicious content
    malicious_result = _check_malicious_content(content)
    if malicious_result:
        return malicious_result
    
    # Check line count
    lines = content.split('\n')
    max_lines = 10000
    if len(lines) > max_lines:
        return ValidationResult(
            False,
            f"File has too many lines: {len(lines)}. Maximum: {max_lines}",
            "TOO_MANY_LINES"
        )
    
    # Check for extremely long lines
    max_line_length = 10000
    for i, line in enumerate(lines, 1):
        if len(line) > max_line_length:
            return ValidationResult(
                False,
                f"Line {i} is too long: {len(line)} characters. Maximum: {max_line_length}",
                "LINE_TOO_LONG"
            )
    
    # Validate based on file extension
    file_ext = Path(filename).suffix.lower()
    ext_result = _validate_by_extension(content, file_ext)
    if ext_result:
        return ext_result
    
    return None  # Valid


def detect_language_from_filename(filename: str) -> Optional[str]:
    """
    Detect programming language from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        Detected language name or None if not detected
    """
    if not filename:
        return None
    
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    
    # Language mapping based on file extensions
    extension_to_language = {
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.py': 'python',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.cs': 'csharp',
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.json': 'json',
        '.xml': 'xml',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.sh': 'bash',
        '.bash': 'bash',
        '.sql': 'sql',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.md': 'markdown',
        '.dockerfile': 'dockerfile'
    }
    
    # Check extension mapping
    if extension in extension_to_language:
        return extension_to_language[extension]
    
    # Check filename patterns for special cases
    filename_lower = filename.lower()
    
    if filename_lower in ['dockerfile', 'dockerfile.dev', 'dockerfile.prod']:
        return 'dockerfile'
    
    if filename_lower in ['makefile', 'makefile.am', 'makefile.in']:
        return 'makefile'
    
    if filename_lower.startswith('jenkinsfile'):
        return 'groovy'
    
    if filename_lower.endswith('.config.js') or filename_lower.endswith('.config.ts'):
        return 'javascript' if filename_lower.endswith('.js') else 'typescript'
    
    return None


def _contains_binary_content(content: str) -> bool:
    """Check if content contains binary data."""
    # Check for null bytes
    if '\x00' in content:
        return True
    
    # Check for high ratio of non-printable characters
    printable_chars = sum(1 for c in content if c.isprintable() or c in '\n\r\t')
    if len(content) > 0:
        printable_ratio = printable_chars / len(content)
        if printable_ratio < 0.7:  # Less than 70% printable characters
            return True
    
    return False


def _check_malicious_content(content: str) -> Optional[ValidationResult]:
    """Check for potentially malicious content patterns."""
    # Patterns that might indicate malicious code
    malicious_patterns = [
        # Script injection patterns
        (r'<script[^>]*>', 'Potential script injection'),
        (r'javascript:', 'JavaScript protocol detected'),
        (r'data:text/html', 'Data URI with HTML detected'),
        (r'eval\s*\(', 'eval() function detected'),
        (r'exec\s*\(', 'exec() function detected'),
        
        # Command injection patterns
        (r'system\s*\(', 'System command execution detected'),
        (r'shell_exec\s*\(', 'Shell execution detected'),
        (r'passthru\s*\(', 'Passthru execution detected'),
        
        # File system access patterns (be careful with legitimate use)
        (r'\.\./', 'Directory traversal pattern detected'),
        (r'\.\.\\', 'Directory traversal pattern detected'),
        
        # SQL injection patterns
        (r'union\s+select', 'Potential SQL injection'),
        (r'drop\s+table', 'Potential destructive SQL'),
        
        # Network access patterns
        (r'curl\s+-', 'External network request detected'),
        (r'wget\s+', 'External network request detected'),
    ]
    
    content_lower = content.lower()
    
    for pattern, message in malicious_patterns:
        if re.search(pattern, content_lower, re.IGNORECASE):
            return ValidationResult(
                False,
                f"Security concern: {message}",
                "SECURITY_RISK"
            )
    
    return None


def _validate_by_extension(content: str, extension: str) -> Optional[ValidationResult]:
    """Validate content based on file extension."""
    if extension == '.json':
        return _validate_json_content(content)
    elif extension in ['.yml', '.yaml']:
        return _validate_yaml_content(content)
    elif extension == '.xml':
        return _validate_xml_content(content)
    
    return None


def _validate_json_content(content: str) -> Optional[ValidationResult]:
    """Validate JSON content."""
    try:
        import json
        json.loads(content)
        return None
    except json.JSONDecodeError as e:
        return ValidationResult(
            False,
            f"Invalid JSON: {str(e)}",
            "INVALID_JSON"
        )


def _validate_yaml_content(content: str) -> Optional[ValidationResult]:
    """Validate YAML content."""
    try:
        import yaml
        yaml.safe_load(content)
        return None
    except yaml.YAMLError as e:
        return ValidationResult(
            False,
            f"Invalid YAML: {str(e)}",
            "INVALID_YAML"
        )
    except ImportError:
        # YAML library not available, skip validation
        return None


def _validate_xml_content(content: str) -> Optional[ValidationResult]:
    """Validate XML content."""
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(content)
        return None
    except ET.ParseError as e:
        return ValidationResult(
            False,
            f"Invalid XML: {str(e)}",
            "INVALID_XML"
        )


def get_supported_extensions() -> set:
    """Get set of supported file extensions."""
    return {
        '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.c', '.cpp', '.cc', '.cxx',
        '.cs', '.html', '.htm', '.css', '.json', '.xml', '.php', '.rb', '.go', 
        '.rs', '.swift', '.kt', '.scala', '.sh', '.bash', '.sql', '.yml', '.yaml',
        '.md'
    }


def is_supported_file(filename: str) -> bool:
    """Check if file is supported for analysis."""
    extension = Path(filename).suffix.lower()
    return extension in get_supported_extensions()


def get_mime_type(filename: str) -> Optional[str]:
    """Get MIME type for a filename."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type


def validate_filename(filename: str) -> Optional[ValidationResult]:
    """
    Validate filename for security and format.
    
    Args:
        filename: The filename to validate
        
    Returns:
        ValidationResult if validation fails, None if valid
    """
    if not filename:
        return ValidationResult(False, "Filename is empty", "EMPTY_FILENAME")
    
    # Check filename length
    if len(filename) > 255:
        return ValidationResult(
            False,
            f"Filename too long: {len(filename)} characters. Maximum: 255",
            "FILENAME_TOO_LONG"
        )
    
    # Check for dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
    for char in dangerous_chars:
        if char in filename:
            return ValidationResult(
                False,
                f"Filename contains dangerous character: {char}",
                "DANGEROUS_CHARACTER"
            )
    
    # Check for path traversal
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        return ValidationResult(
            False,
            "Filename contains path traversal patterns",
            "PATH_TRAVERSAL"
        )
    
    # Check if it's a supported file type
    if not is_supported_file(filename):
        extension = Path(filename).suffix.lower()
        return ValidationResult(
            False,
            f"Unsupported file type: {extension}",
            "UNSUPPORTED_TYPE"
        )
    
    return None