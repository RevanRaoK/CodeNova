"""
GitHub OAuth Pydantic Schemas

Pydantic models for GitHub OAuth API request/response validation.

Requirements covered: 3.1, 3.2
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class GitHubOAuthInitiateResponse(BaseModel):
    """Response model for OAuth flow initiation."""
    
    authorization_url: str = Field(..., description="GitHub authorization URL to redirect user to")
    state: str = Field(..., description="OAuth state parameter for CSRF protection")
    expires_in: int = Field(..., description="State expiration time in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GitHubOAuthCallbackResponse(BaseModel):
    """Response model for OAuth callback processing."""
    
    integration_id: str = Field(..., description="GitHub integration ID")
    github_username: str = Field(..., description="GitHub username")
    github_user_id: int = Field(..., description="GitHub user ID")
    redirect_url: Optional[str] = Field(None, description="URL to redirect to after OAuth")
    scopes: List[str] = Field(default_factory=list, description="Granted OAuth scopes")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GitHubOAuthStatusResponse(BaseModel):
    """Response model for OAuth integration status."""
    
    connected: bool = Field(..., description="Whether GitHub is connected")
    github_username: Optional[str] = Field(None, description="GitHub username if connected")
    github_user_id: Optional[int] = Field(None, description="GitHub user ID if connected")
    integration_id: Optional[str] = Field(None, description="Integration ID if connected")
    scopes: List[str] = Field(default_factory=list, description="Granted OAuth scopes")
    connected_at: Optional[datetime] = Field(None, description="When integration was created")
    last_used: Optional[datetime] = Field(None, description="When integration was last used")
    token_valid: bool = Field(False, description="Whether the stored token is still valid")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GitHubOAuthIntegrationResponse(BaseModel):
    """Response model for detailed GitHub integration information."""
    
    id: str = Field(..., description="Integration ID")
    github_user_id: int = Field(..., description="GitHub user ID")
    github_username: str = Field(..., description="GitHub username")
    github_email: Optional[str] = Field(None, description="GitHub email address")
    github_name: Optional[str] = Field(None, description="GitHub display name")
    scopes: List[str] = Field(default_factory=list, description="Granted OAuth scopes")
    token_scopes: List[str] = Field(default_factory=list, description="Current token scopes")
    token_valid: bool = Field(..., description="Whether the token is currently valid")
    created_at: datetime = Field(..., description="When integration was created")
    updated_at: datetime = Field(..., description="When integration was last updated")
    last_used: Optional[datetime] = Field(None, description="When integration was last used")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GitHubOAuthInitiateRequest(BaseModel):
    """Request model for OAuth flow initiation."""
    
    redirect_url: Optional[str] = Field(
        None, 
        description="URL to redirect to after OAuth completion",
        max_length=1000
    )
    scopes: Optional[List[str]] = Field(
        None,
        description="Custom OAuth scopes to request"
    )
    
    @validator('redirect_url')
    def validate_redirect_url(cls, v):
        """Validate redirect URL format."""
        if v is not None:
            # Basic URL validation
            if not v.startswith(('http://', 'https://', '/')):
                raise ValueError('Redirect URL must be a valid HTTP/HTTPS URL or relative path')
            if len(v) > 1000:
                raise ValueError('Redirect URL too long')
        return v
    
    @validator('scopes')
    def validate_scopes(cls, v):
        """Validate OAuth scopes."""
        if v is not None:
            # Valid GitHub OAuth scopes
            valid_scopes = {
                'repo', 'repo:status', 'repo_deployment', 'public_repo',
                'repo:invite', 'security_events', 'admin:repo_hook',
                'write:repo_hook', 'read:repo_hook', 'admin:org',
                'write:org', 'read:org', 'admin:public_key',
                'write:public_key', 'read:public_key', 'admin:org_hook',
                'gist', 'notifications', 'user', 'read:user',
                'user:email', 'user:follow', 'delete_repo',
                'write:discussion', 'read:discussion', 'admin:gpg_key',
                'write:gpg_key', 'read:gpg_key'
            }
            
            for scope in v:
                if scope not in valid_scopes:
                    raise ValueError(f'Invalid OAuth scope: {scope}')
        return v


class GitHubTokenValidationResponse(BaseModel):
    """Response model for token validation."""
    
    valid: bool = Field(..., description="Whether the token is valid")
    github_user_id: Optional[int] = Field(None, description="GitHub user ID if valid")
    github_username: Optional[str] = Field(None, description="GitHub username if valid")
    scopes: List[str] = Field(default_factory=list, description="Token scopes if valid")
    last_validated: str = Field(..., description="Validation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GitHubOAuthErrorResponse(BaseModel):
    """Response model for OAuth errors."""
    
    error: str = Field(..., description="Error code")
    error_description: Optional[str] = Field(None, description="Human-readable error description")
    error_uri: Optional[str] = Field(None, description="URI with error information")
    state: Optional[str] = Field(None, description="State parameter if available")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GitHubOAuthCleanupResponse(BaseModel):
    """Response model for OAuth state cleanup."""
    
    message: str = Field(..., description="Cleanup result message")
    cleaned_count: int = Field(..., description="Number of expired states cleaned up")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }