"""
Comprehensive error handling with user-friendly messages.

This module provides centralized error handling, custom exceptions,
and user-friendly error responses for the CodeNova platform.

Requirements covered: 12.3, 12.4, 12.5
"""

from typing import Optional, Dict, Any, Union
from datetime import datetime
import traceback
import uuid

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.monitoring import get_service_logger, ServiceType

logger = get_service_logger(ServiceType.API, "error_handler")


class BaseAPIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "internal_error",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(BaseAPIException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="validation_error",
            details=details or {}
        )
        if field:
            self.details["field"] = field


class AuthenticationException(BaseAPIException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="authentication_error",
            details=details or {}
        )


class AuthorizationException(BaseAPIException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="authorization_error",
            details=details or {}
        )


class ResourceNotFoundException(BaseAPIException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, resource_id: Union[str, int], details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="resource_not_found",
            details=details or {}
        )
        self.details["resource"] = resource
        self.details["resource_id"] = str(resource_id)


class ConflictException(BaseAPIException):
    """Exception for conflict errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="conflict_error",
            details=details or {}
        )


class RateLimitException(BaseAPIException):
    """Exception for rate limit errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=429,
            error_code="rate_limit_exceeded",
            details=details or {}
        )
        self.details["retry_after"] = retry_after


class ServiceUnavailableException(BaseAPIException):
    """Exception for service unavailable errors."""
    
    def __init__(self, service: str, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message or f"{service} is temporarily unavailable",
            status_code=503,
            error_code="service_unavailable",
            details=details or {}
        )
        self.details["service"] = service


class FileUploadException(BaseAPIException):
    """Exception for file upload errors."""
    
    def __init__(self, message: str, filename: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="file_upload_error",
            details=details or {}
        )
        if filename:
            self.details["filename"] = filename


class AnalysisException(BaseAPIException):
    """Exception for code analysis errors."""
    
    def __init__(self, message: str, analysis_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="analysis_error",
            details=details or {}
        )
        if analysis_id:
            self.details["analysis_id"] = analysis_id


class ErrorResponse:
    """Standardized error response format."""
    
    @staticmethod
    def create(
        error_code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "error": error_code,
            "message": message,
            "status_code": status_code,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id or str(uuid.uuid4())
        }
    
    @staticmethod
    def user_friendly_message(error_code: str, original_message: str) -> str:
        """Convert technical error messages to user-friendly messages."""
        friendly_messages = {
            "validation_error": "Please check your input and try again.",
            "authentication_error": "Please log in to continue.",
            "authorization_error": "You don't have permission to perform this action.",
            "resource_not_found": "The requested resource was not found.",
            "conflict_error": "This action conflicts with existing data.",
            "rate_limit_exceeded": "You're making too many requests. Please wait and try again.",
            "service_unavailable": "This service is temporarily unavailable. Please try again later.",
            "file_upload_error": "There was a problem uploading your file.",
            "analysis_error": "There was a problem analyzing your code.",
            "internal_error": "An unexpected error occurred. Please try again."
        }
        
        return friendly_messages.get(error_code, original_message)


class ErrorHandler:
    """Centralized error handling service."""
    
    @staticmethod
    async def handle_base_api_exception(request: Request, exc: BaseAPIException) -> JSONResponse:
        """Handle BaseAPIException."""
        request_id = str(uuid.uuid4())
        
        logger.error(
            "API exception",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            request_id=request_id,
            path=request.url.path,
            method=request.method
        )
        
        response = ErrorResponse.create(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response
        )
    
    @staticmethod
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTPException."""
        request_id = str(uuid.uuid4())
        
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            request_id=request_id,
            path=request.url.path,
            method=request.method
        )
        
        # Map status codes to error codes
        error_code_map = {
            400: "bad_request",
            401: "authentication_error",
            403: "authorization_error",
            404: "resource_not_found",
            409: "conflict_error",
            429: "rate_limit_exceeded",
            500: "internal_error",
            503: "service_unavailable"
        }
        
        error_code = error_code_map.get(exc.status_code, "http_error")
        message = str(exc.detail) if exc.detail else "An error occurred"
        
        response = ErrorResponse.create(
            error_code=error_code,
            message=message,
            status_code=exc.status_code,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response,
            headers=exc.headers
        )
    
    @staticmethod
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        request_id = str(uuid.uuid4())
        
        # Extract validation errors
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.warning(
            "Validation error",
            errors=errors,
            request_id=request_id,
            path=request.url.path,
            method=request.method
        )
        
        response = ErrorResponse.create(
            error_code="validation_error",
            message="Invalid input data",
            status_code=422,
            details={"errors": errors},
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=422,
            content=response
        )
    
    @staticmethod
    async def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Handle database errors."""
        request_id = str(uuid.uuid4())
        
        logger.error(
            "Database error",
            error=str(exc),
            error_type=type(exc).__name__,
            request_id=request_id,
            path=request.url.path,
            method=request.method
        )
        
        # Check for specific database errors
        if isinstance(exc, IntegrityError):
            message = "This operation conflicts with existing data"
            error_code = "conflict_error"
            status_code = 409
        else:
            message = "A database error occurred"
            error_code = "database_error"
            status_code = 500
        
        response = ErrorResponse.create(
            error_code=error_code,
            message=message,
            status_code=status_code,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status_code,
            content=response
        )
    
    @staticmethod
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle generic exceptions."""
        request_id = str(uuid.uuid4())
        
        # Log full traceback for debugging
        logger.error(
            "Unhandled exception",
            error=str(exc),
            error_type=type(exc).__name__,
            traceback=traceback.format_exc(),
            request_id=request_id,
            path=request.url.path,
            method=request.method
        )
        
        response = ErrorResponse.create(
            error_code="internal_error",
            message="An unexpected error occurred",
            status_code=500,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=500,
            content=response
        )


def register_error_handlers(app):
    """Register all error handlers with the FastAPI app."""
    
    # Custom API exceptions
    @app.exception_handler(BaseAPIException)
    async def base_api_exception_handler(request: Request, exc: BaseAPIException):
        return await ErrorHandler.handle_base_api_exception(request, exc)
    
    # FastAPI HTTP exceptions
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return await ErrorHandler.handle_http_exception(request, exc)
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        return await ErrorHandler.handle_http_exception(request, HTTPException(status_code=exc.status_code, detail=exc.detail))
    
    # Validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return await ErrorHandler.handle_validation_error(request, exc)
    
    # Database errors
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        return await ErrorHandler.handle_database_error(request, exc)
    
    # Generic exceptions
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return await ErrorHandler.handle_generic_exception(request, exc)
    
    logger.info("Error handlers registered successfully")


# Retry mechanism decorator
from functools import wraps
import asyncio


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry failed operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_retries}",
                            function=func.__name__,
                            error=str(e),
                            delay=current_delay
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All retry attempts failed",
                            function=func.__name__,
                            error=str(e),
                            attempts=max_retries + 1
                        )
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_retries}",
                            function=func.__name__,
                            error=str(e),
                            delay=current_delay
                        )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All retry attempts failed",
                            function=func.__name__,
                            error=str(e),
                            attempts=max_retries + 1
                        )
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
