"""
Core exceptions for the application.

This module defines custom exception classes used throughout the application
for better error handling and debugging.
"""


class CodeNovaException(Exception):
    """Base exception class for CodeNova application."""
    pass


class AuthenticationError(CodeNovaException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(CodeNovaException):
    """Raised when user lacks required permissions."""
    pass


class ValidationError(CodeNovaException):
    """Raised when data validation fails."""
    pass


class NotFoundError(CodeNovaException):
    """Raised when a requested resource is not found."""
    pass


class ConflictError(CodeNovaException):
    """Raised when there's a conflict with existing data."""
    pass


class DatabaseError(CodeNovaException):
    """Raised when database operations fail."""
    pass


class ExternalServiceError(CodeNovaException):
    """Raised when external service calls fail."""
    pass


class GitHubIntegrationError(ExternalServiceError):
    """Raised when GitHub integration operations fail."""
    pass


class AnalysisError(CodeNovaException):
    """Raised when code analysis operations fail."""
    pass


class FileStorageError(ExternalServiceError):
    """Raised when file storage operations fail."""
    pass


class QueueError(CodeNovaException):
    """Raised when queue operations fail."""
    pass


class CacheError(CodeNovaException):
    """Raised when cache operations fail."""
    pass


class ConfigurationError(CodeNovaException):
    """Raised when configuration is invalid or missing."""
    pass