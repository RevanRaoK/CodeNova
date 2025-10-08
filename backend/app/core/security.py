"""    
Security hardening and rate limiting for all platform services.

This module provides comprehensive security measures including rate limiting,
input validation, authentication hardening, and security monitoring.

Requirements covered: Performance and scalability for all features
"""

import hashlib
import hmac
import secrets
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from functools import wraps
import re
import ipaddress
from urllib.parse import urlparse

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cache import cache, RateLimitCache
from app.core.monitoring import get_service_logger, ServiceType, monitor_performance
from app.core.database import get_db

logger = get_service_logger(ServiceType.API, "security")


class SecurityConfig:
    """Security configuration constants."""
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = 100  # requests per hour
    AUTH_RATE_LIMIT = 10      # auth attempts per hour
    API_RATE_LIMIT = 1000     # API calls per hour
    UPLOAD_RATE_LIMIT = 20    # file uploads per hour
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    
    # JWT settings
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    
    # Blocked user agents and IPs
    BLOCKED_USER_AGENTS = [
        r".*bot.*", r".*crawler.*", r".*spider.*", r".*scraper.*"
    ]
    
    # Allowed file types for uploads
    ALLOWED_FILE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
        '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.md', '.txt'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class RateLimiter:
    """Advanced rate limiting with multiple strategies."""
    
    @staticmethod
    def check_rate_limit(
        identifier: str,
        limit: int,
        window: int = 3600,
        endpoint: str = "default"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limit with sliding window algorithm.
        
        Returns:
            Tuple of (allowed, info_dict)
        """
        cache_key = f"rate_limit:{identifier}:{endpoint}"
        
        # Get current window data
        current_time = int(time.time())
        window_start = current_time - window
        
        # Get existing requests in current window
        requests = cache.get(cache_key) or []
        
        # Filter requests within current window
        valid_requests = [req_time for req_time in requests if req_time > window_start]
        
        # Check if limit exceeded
        if len(valid_requests) >= limit:
            next_reset = min(valid_requests) + window
            return False, {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "reset_time": next_reset,
                "retry_after": next_reset - current_time
            }
        
        # Add current request
        valid_requests.append(current_time)
        cache.set(cache_key, valid_requests, window)
        
        return True, {
            "allowed": True,
            "limit": limit,
            "remaining": limit - len(valid_requests),
            "reset_time": current_time + window,
            "retry_after": 0
        }
    
    @staticmethod
    def get_client_identifier(request: Request) -> str:
        """Get unique identifier for rate limiting."""
        # Try to get user ID from token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[SecurityConfig.JWT_ALGORITHM])
                return f"user:{payload.get('sub')}"
            except:
                pass
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"


def rate_limit(limit: int = SecurityConfig.DEFAULT_RATE_LIMIT, window: int = 3600, endpoint: str = None):
    """Rate limiting decorator for API endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            endpoint_name = endpoint or f"{request.method}:{request.url.path}"
            identifier = RateLimiter.get_client_identifier(request)
            
            allowed, info = RateLimiter.check_rate_limit(identifier, limit, window, endpoint_name)
            
            if not allowed:
                logger.warning(
                    "Rate limit exceeded",
                    identifier=identifier,
                    endpoint=endpoint_name,
                    limit=limit,
                    retry_after=info["retry_after"]
                )
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": str(info["remaining"]),
                        "X-RateLimit-Reset": str(info["reset_time"]),
                        "Retry-After": str(info["retry_after"])
                    }
                )
            
            # Add rate limit headers to response
            response = await func(request, *args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(info["reset_time"])
            
            return response
        return wrapper
    return decorator


class InputValidator:
    """Input validation and sanitization utilities."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, List[str]]:
        """Validate password strength."""
        errors = []
        
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters")
        
        if len(password) > SecurityConfig.MAX_PASSWORD_LENGTH:
            errors.append(f"Password must be no more than {SecurityConfig.MAX_PASSWORD_LENGTH} characters")
        
        if SecurityConfig.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if SecurityConfig.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if SecurityConfig.REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if SecurityConfig.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin']:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Remove or replace dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
        
        return filename
    
    @staticmethod
    def validate_file_upload(filename: str, content_type: str, file_size: int) -> Tuple[bool, str]:
        """Validate file upload parameters."""
        # Check file size
        if file_size > SecurityConfig.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum allowed size of {SecurityConfig.MAX_FILE_SIZE} bytes"
        
        # Check file extension
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        if file_ext not in SecurityConfig.ALLOWED_FILE_EXTENSIONS:
            return False, f"File type {file_ext} is not allowed"
        
        # Check for executable files
        executable_extensions = {'.exe', '.bat', '.cmd', '.com', '.scr', '.pif'}
        if file_ext in executable_extensions:
            return False, "Executable files are not allowed"
        
        return True, "Valid file"
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and safety."""
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Only allow http/https
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Block localhost and private IPs
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private or ip.is_loopback:
                    return False
            except:
                pass  # Not an IP address, continue validation
            
            return True
        except:
            return False


class PasswordManager:
    """Secure password hashing and verification."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            return False
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_urlsafe(length)


class JWTManager:
    """JWT token management with security features."""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=SecurityConfig.JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """Create JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(16)  # Unique token ID
        }
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=SecurityConfig.JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[SecurityConfig.JWT_ALGORITHM])
            
            if payload.get("type") != token_type:
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired", token_type=token_type)
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token", error=str(e), token_type=token_type)
            return None


class SecurityMiddleware:
    """Security middleware for request processing."""
    
    @staticmethod
    def check_user_agent(request: Request) -> bool:
        """Check if user agent is blocked."""
        user_agent = request.headers.get("User-Agent", "").lower()
        
        for pattern in SecurityConfig.BLOCKED_USER_AGENTS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response."""
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
    
    @staticmethod
    def validate_request_size(request: Request, max_size: int = 10 * 1024 * 1024):
        """Validate request content length."""
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > max_size:
            raise HTTPException(status_code=413, detail="Request entity too large")


class WebhookSecurity:
    """Security utilities for webhook verification."""
    
    @staticmethod
    def verify_github_webhook(payload: bytes, signature: str, secret: str) -> bool:
        """Verify GitHub webhook signature."""
        if not signature.startswith('sha256='):
            return False
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        received_signature = signature[7:]  # Remove 'sha256=' prefix
        
        return hmac.compare_digest(expected_signature, received_signature)
    
    @staticmethod
    def verify_webhook_timestamp(timestamp: str, tolerance: int = 300) -> bool:
        """Verify webhook timestamp to prevent replay attacks."""
        try:
            webhook_time = int(timestamp)
            current_time = int(time.time())
            
            return abs(current_time - webhook_time) <= tolerance
        except:
            return False


class SecurityAuditLogger:
    """Security event logging and monitoring."""
    
    def __init__(self):
        self.logger = get_service_logger(ServiceType.API, "security_audit")
    
    def log_authentication_attempt(self, email: str, success: bool, ip_address: str, user_agent: str):
        """Log authentication attempt."""
        self.logger.info(
            "Authentication attempt",
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            event_type="auth_attempt"
        )
    
    def log_permission_denied(self, user_id: int, resource: str, action: str, ip_address: str):
        """Log permission denied event."""
        self.logger.warning(
            "Permission denied",
            user_id=user_id,
            resource=resource,
            action=action,
            ip_address=ip_address,
            event_type="permission_denied"
        )
    
    def log_suspicious_activity(self, description: str, user_id: int = None, ip_address: str = None, **kwargs):
        """Log suspicious activity."""
        self.logger.warning(
            "Suspicious activity detected",
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            event_type="suspicious_activity",
            **kwargs
        )
    
    def log_security_event(self, event_type: str, severity: str, description: str, **kwargs):
        """Log general security event."""
        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method(
            description,
            event_type=event_type,
            severity=severity,
            **kwargs
        )


# Global security audit logger
security_audit = SecurityAuditLogger()

# Password utility functions (for backward compatibility)
def get_password_hash(password: str) -> str:
    """Hash password using bcrypt."""
    return PasswordManager.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return PasswordManager.verify_password(plain_password, hashed_password)

# JWT utility functions (for backward compatibility)
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    return JWTManager.create_access_token(data, expires_delta)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token."""
    user_id = data.get("sub")
    if user_id:
        return JWTManager.create_refresh_token(int(user_id))
    raise ValueError("User ID required for refresh token")

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token."""
    return JWTManager.verify_token(token, token_type)

# Token expiration constants
ACCESS_TOKEN_EXPIRE_MINUTES = SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES

# Security dependency functions for FastAPI
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user."""
    token = credentials.credentials
    payload = JWTManager.verify_token(token, "access")
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Get user from database
    from app.models import User
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user


async def require_admin(current_user = Depends(get_current_user)):
    """Require admin role."""
    from app.models import UserRole
    if current_user.role != UserRole.ADMIN:
        security_audit.log_permission_denied(
            user_id=current_user.id,
            resource="admin",
            action="access",
            ip_address="unknown"
        )
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def security_headers_middleware(request: Request, call_next):
    """Middleware to add security headers."""
    async def middleware(request: Request):
        # Check user agent
        if not SecurityMiddleware.check_user_agent(request):
            raise HTTPException(status_code=403, detail="Blocked user agent")
        
        # Validate request size
        SecurityMiddleware.validate_request_size(request)
        
        response = await call_next(request)
        
        # Add security headers
        SecurityMiddleware.add_security_headers(response)
        
        return response
    
    return middleware(request)