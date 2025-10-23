"""
Unit tests for FileValidationService.

Tests cover:
- File type validation
- File size validation
- MIME type validation
- Content validation
- Code content validation

Requirements: 15.1, 15.3, 15.4
"""

import pytest
from io import BytesIO
from unittest.mock import Mock, AsyncMock, patch
from fastapi import UploadFile

from app.services.file_validation_service import FileValidationService, ValidationResult


class TestFileValidationService:
    """Test suite for FileValidationService."""
    
    @pytest.fixture
    def service(self):
        """Create a FileValidationService instance."""
        return FileValidationService()
    
    def create_upload_file(self, filename: str, content: bytes, content_type: str = "text/plain"):
        """Helper to create a mock UploadFile."""
        file = Mock(spec=UploadFile)
        file.filename = filename
        file.content_type = content_type
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        return file
    
    # Extension Validation Tests
    
    @pytest.mark.unit
    def test_validate_extension_valid_python(self, service):
        """Test validation of valid Python file extension."""
        result = service._validate_extension("test.py")
        assert result.is_valid is True
        assert result.error_message is None
    
    @pytest.mark.unit
    def test_validate_extension_valid_javascript(self, service):
        """Test validation of valid JavaScript file extension."""
        result = service._validate_extension("app.js")
        assert result.is_valid is True
    
    @pytest.mark.unit
    def test_validate_extension_valid_typescript(self, service):
        """Test validation of valid TypeScript file extension."""
        result = service._validate_extension("component.tsx")
        assert result.is_valid is True
    
    @pytest.mark.unit
    def test_validate_extension_no_extension(self, service):
        """Test validation fails for file without extension."""
        result = service._validate_extension("README")
        assert result.is_valid is False
        assert result.error_code == "NO_EXTENSION"
        assert "must have an extension" in result.error_message
    
    @pytest.mark.unit
    def test_validate_extension_unsupported(self, service):
        """Test validation fails for unsupported extension."""
        result = service._validate_extension("document.pdf")
        assert result.is_valid is False
        assert result.error_code == "UNSUPPORTED_EXTENSION"
        assert "not supported" in result.error_message
    
    # Dangerous Extension Tests
    
    @pytest.mark.unit
    def test_check_dangerous_extension_exe(self, service):
        """Test rejection of executable files."""
        result = service._check_dangerous_extension("malware.exe")
        assert result.is_valid is False
        assert result.error_code == "DANGEROUS_EXTENSION"
        assert "not allowed for security reasons" in result.error_message
    
    @pytest.mark.unit
    def test_check_dangerous_extension_zip(self, service):
        """Test rejection of archive files."""
        result = service._check_dangerous_extension("archive.zip")
        assert result.is_valid is False
        assert result.error_code == "DANGEROUS_EXTENSION"
    
    @pytest.mark.unit
    def test_check_dangerous_extension_safe(self, service):
        """Test acceptance of safe file extensions."""
        result = service._check_dangerous_extension("script.py")
        assert result.is_valid is True
    
    # Size Validation Tests
    
    @pytest.mark.unit
    def test_validate_size_empty_file(self, service):
        """Test validation fails for empty file."""
        result = service._validate_size(b"", "test.py")
        assert result.is_valid is False
        assert result.error_code == "EMPTY_FILE"
    
    @pytest.mark.unit
    def test_validate_size_valid_small_file(self, service):
        """Test validation passes for small file."""
        content = b"print('hello world')"
        result = service._validate_size(content, "test.py")
        assert result.is_valid is True
        assert len(result.warnings) == 0
    
    @pytest.mark.unit
    def test_validate_size_file_too_large(self, service):
        """Test validation fails for file exceeding size limit."""
        # Create 6MB file (exceeds 5MB limit)
        content = b"x" * (6 * 1024 * 1024)
        result = service._validate_size(content, "large.py")
        assert result.is_valid is False
        assert result.error_code == "FILE_TOO_LARGE"
        assert "exceeds maximum" in result.error_message
    
    @pytest.mark.unit
    def test_validate_size_warning_near_limit(self, service):
        """Test warning for file near size limit."""
        # Create 4.5MB file (90% of 5MB limit)
        content = b"x" * int(4.5 * 1024 * 1024)
        result = service._validate_size(content, "large.py")
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "close to the maximum limit" in result.warnings[0]
    
    # Content Validation Tests
    
    @pytest.mark.unit
    def test_validate_content_valid_utf8(self, service):
        """Test validation of valid UTF-8 text content."""
        content = "def hello():\n    print('Hello, World!')".encode('utf-8')
        result = service._validate_content(content, "test.py")
        assert result.is_valid is True
    
    @pytest.mark.unit
    def test_validate_content_binary_with_null_bytes(self, service):
        """Test rejection of binary content with null bytes."""
        content = b"text\x00binary"
        result = service._validate_content(content, "test.py")
        assert result.is_valid is False
        assert result.error_code == "BINARY_CONTENT"
    
    @pytest.mark.unit
    def test_validate_content_only_whitespace(self, service):
        """Test rejection of file with only whitespace."""
        content = b"   \n\n\t\t   \n"
        result = service._validate_content(content, "test.py")
        assert result.is_valid is False
        assert result.error_code == "EMPTY_CONTENT"
    
    @pytest.mark.unit
    def test_validate_content_latin1_encoding(self, service):
        """Test handling of non-UTF-8 encoding."""
        # Content with Latin-1 characters
        content = "café".encode('latin-1')
        result = service._validate_content(content, "test.py")
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "latin-1" in result.warnings[0].lower()
    
    # Line Count Validation Tests
    
    @pytest.mark.unit
    def test_validate_line_count_normal(self, service):
        """Test validation of file with normal line count."""
        content = "\n".join([f"line {i}" for i in range(100)]).encode('utf-8')
        result = service._validate_line_count(content, "test.py")
        assert result.is_valid is True
        assert len(result.warnings) == 0
    
    @pytest.mark.unit
    def test_validate_line_count_too_many_lines(self, service):
        """Test rejection of file with too many lines."""
        # Create file with more than MAX_LINES (10000)
        content = "\n".join([f"line {i}" for i in range(10001)]).encode('utf-8')
        result = service._validate_line_count(content, "test.py")
        assert result.is_valid is False
        assert result.error_code == "TOO_MANY_LINES"
        assert "exceeding maximum" in result.error_message
    
    @pytest.mark.unit
    def test_validate_line_count_warning_near_limit(self, service):
        """Test warning for file approaching line limit."""
        # Create file with 9000 lines (90% of 10000 limit)
        content = "\n".join([f"line {i}" for i in range(9000)]).encode('utf-8')
        result = service._validate_line_count(content, "test.py")
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "approaching the maximum limit" in result.warnings[0]
    
    # Full File Validation Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_file_valid_python_file(self, service):
        """Test complete validation of valid Python file."""
        content = b"def hello():\n    print('Hello, World!')"
        file = self.create_upload_file("test.py", content)
        
        with patch('magic.from_buffer', return_value='text/x-python'):
            result = await service.validate_file(file)
        
        assert result.is_valid is True
        assert result.file_info is not None
        assert result.file_info["filename"] == "test.py"
        assert result.file_info["extension"] == "py"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_file_no_filename(self, service):
        """Test validation fails when filename is missing."""
        file = self.create_upload_file("", b"content")
        result = await service.validate_file(file)
        
        assert result.is_valid is False
        assert result.error_code == "MISSING_FILENAME"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_file_unsupported_type(self, service):
        """Test validation fails for unsupported file type."""
        content = b"PDF content"
        file = self.create_upload_file("document.pdf", content)
        
        result = await service.validate_file(file)
        assert result.is_valid is False
        assert result.error_code == "UNSUPPORTED_EXTENSION"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_file_read_error(self, service):
        """Test handling of file read errors."""
        file = Mock(spec=UploadFile)
        file.filename = "test.py"
        file.read = AsyncMock(side_effect=Exception("Read failed"))
        
        result = await service.validate_file(file)
        assert result.is_valid is False
        assert result.error_code == "READ_ERROR"
        assert "Failed to read file content" in result.error_message
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_file_javascript(self, service):
        """Test validation of JavaScript file."""
        content = b"function hello() { console.log('Hello'); }"
        file = self.create_upload_file("app.js", content, "application/javascript")
        
        with patch('magic.from_buffer', return_value='application/javascript'):
            result = await service.validate_file(file)
        
        assert result.is_valid is True
        assert result.file_info["extension"] == "js"
    
    # Code Content Validation Tests
    
    @pytest.mark.unit
    def test_validate_code_content_valid(self, service):
        """Test validation of valid code content."""
        code = "def hello():\n    print('Hello')"
        result = service.validate_code_content(code, "python")
        
        assert result.is_valid is True
        assert result.file_info is not None
        assert result.file_info["language"] == "python"
    
    @pytest.mark.unit
    def test_validate_code_content_empty(self, service):
        """Test rejection of empty code."""
        result = service.validate_code_content("", "python")
        
        assert result.is_valid is False
        assert result.error_code == "EMPTY_CODE"
    
    @pytest.mark.unit
    def test_validate_code_content_whitespace_only(self, service):
        """Test rejection of whitespace-only code."""
        result = service.validate_code_content("   \n\n\t  ", "python")
        
        assert result.is_valid is False
        assert result.error_code == "EMPTY_CODE"
    
    @pytest.mark.unit
    def test_validate_code_content_too_large(self, service):
        """Test rejection of code exceeding size limit."""
        # Create code larger than 5MB
        code = "x" * (6 * 1024 * 1024)
        result = service.validate_code_content(code, "python")
        
        assert result.is_valid is False
        assert result.error_code == "CODE_TOO_LARGE"
    
    @pytest.mark.unit
    def test_validate_code_content_too_many_lines(self, service):
        """Test rejection of code with too many lines."""
        code = "\n".join([f"line {i}" for i in range(10001)])
        result = service.validate_code_content(code, "python")
        
        assert result.is_valid is False
        assert result.error_code == "TOO_MANY_LINES"
    
    @pytest.mark.unit
    def test_validate_code_content_unsupported_language(self, service):
        """Test rejection of unsupported language."""
        code = "some code"
        result = service.validate_code_content(code, "cobol")
        
        assert result.is_valid is False
        assert result.error_code == "UNSUPPORTED_LANGUAGE"
    
    @pytest.mark.unit
    def test_validate_code_content_supported_languages(self, service):
        """Test validation passes for all supported languages."""
        supported = ['python', 'javascript', 'typescript', 'java', 'cpp']
        code = "function test() { return true; }"
        
        for language in supported:
            result = service.validate_code_content(code, language)
            assert result.is_valid is True, f"Failed for language: {language}"
    
    # Edge Cases
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_file_with_warnings(self, service):
        """Test file validation with warnings but still valid."""
        # Create a large file that triggers warnings
        content = b"x" * int(4.5 * 1024 * 1024)
        file = self.create_upload_file("large.py", content)
        
        with patch('magic.from_buffer', return_value='text/x-python'):
            result = await service.validate_file(file)
        
        assert result.is_valid is True
        assert len(result.warnings) > 0
    
    @pytest.mark.unit
    def test_allowed_extensions_coverage(self, service):
        """Test that all major file types are supported."""
        expected_extensions = ['py', 'js', 'ts', 'java', 'cpp', 'go', 'rs', 'php', 'rb']
        
        for ext in expected_extensions:
            assert ext in service.ALLOWED_EXTENSIONS, f"Extension {ext} not in allowed list"
    
    @pytest.mark.unit
    def test_dangerous_extensions_coverage(self, service):
        """Test that dangerous extensions are properly blocked."""
        dangerous = ['exe', 'dll', 'bat', 'zip', 'tar']
        
        for ext in dangerous:
            assert ext in service.DANGEROUS_EXTENSIONS, f"Extension {ext} not in dangerous list"
