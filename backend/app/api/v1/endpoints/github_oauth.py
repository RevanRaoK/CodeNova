"""
GitHub OAuth API Endpoints

Provides REST API endpoints for GitHub OAuth authentication flow.

Requirements covered: 3.1, 3.2
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.api.deps import get_current_user, get_current_user_optional, get_current_user_async, get_current_user_optional_async
from app.core.database import get_async_db
from app.core.exceptions import GitHubIntegrationError
from app.models.users import User
from app.services.github_oauth_service import GitHubOAuthService
from app.schemas.github_oauth import (
    GitHubOAuthInitiateResponse,
    GitHubOAuthCallbackResponse,
    GitHubOAuthIntegrationResponse,
    GitHubOAuthStatusResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/initiate", response_model=GitHubOAuthInitiateResponse)
async def initiate_github_oauth(
    request: Request,
    redirect_url: Optional[str] = None,
    scopes: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Initiate GitHub OAuth flow.
    
    Args:
        redirect_url: Optional URL to redirect to after OAuth completion
        scopes: Optional comma-separated list of OAuth scopes
        current_user: Optional current authenticated user
        db: Database session
        
    Returns:
        GitHubOAuthInitiateResponse with authorization URL and state
        
    Raises:
        HTTPException: If OAuth initiation fails
    """
    try:
        oauth_service = GitHubOAuthService()
        
        # Parse scopes if provided
        scope_list = None
        if scopes:
            scope_list = [scope.strip() for scope in scopes.split(",")]
        
        # Initiate OAuth flow
        authorization_url, state = await oauth_service.initiate_oauth_flow(
            db=db,
            user_id=current_user.id if current_user else None,
            redirect_url=redirect_url,
            scopes=scope_list
        )
        
        logger.info(f"Initiated GitHub OAuth for user {current_user.id if current_user else 'anonymous'}")
        
        return GitHubOAuthInitiateResponse(
            authorization_url=authorization_url,
            state=state,
            expires_in=600  # 10 minutes
        )
        
    except GitHubIntegrationError as e:
        logger.error(f"GitHub OAuth initiation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during OAuth initiation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/callback")
async def github_oauth_callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    error: Optional[str] = Query(None, description="Error from GitHub OAuth"),
    error_description: Optional[str] = Query(None, description="Error description from GitHub"),
    current_user: Optional[User] = Depends(get_current_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Handle GitHub OAuth callback.
    
    This endpoint processes the OAuth callback from GitHub, exchanges the authorization
    code for an access token, and stores the integration.
    
    Args:
        code: Authorization code from GitHub
        state: State parameter for CSRF protection
        error: Optional error from GitHub OAuth
        error_description: Optional error description
        current_user: Optional current authenticated user
        db: Database session
        
    Returns:
        RedirectResponse to appropriate URL based on OAuth result
        
    Raises:
        HTTPException: If callback processing fails
    """
    try:
        # Handle OAuth errors from GitHub
        if error:
            logger.warning(f"GitHub OAuth error: {error} - {error_description}")
            # Redirect to error page or frontend with error parameters
            error_url = f"/oauth/error?error={error}&description={error_description or ''}"
            return RedirectResponse(url=error_url, status_code=302)
        
        oauth_service = GitHubOAuthService()
        
        # Handle OAuth callback
        result = await oauth_service.handle_oauth_callback(
            db=db,
            code=code,
            state=state,
            user_id=current_user.id if current_user else None
        )
        
        logger.info(f"GitHub OAuth callback successful for user {result.get('github_username')}")
        
        # Determine redirect URL
        redirect_url = result.get("redirect_url")
        if not redirect_url:
            # Default redirect based on user authentication status
            if current_user and result.get('integration_id'):
                redirect_url = "/dashboard?github_connected=true"
            else:
                # Unauthenticated user - redirect to login with GitHub info
                redirect_url = f"/login?github_user={result.get('github_username')}&github_oauth=pending"
        
        # Add success parameters to redirect URL
        separator = "&" if "?" in redirect_url else "?"
        if result.get('integration_id'):
            redirect_url += f"{separator}github_integration_id={result['integration_id']}"
        else:
            # For unauthenticated flows, add GitHub user info and temp data ID
            redirect_url += f"{separator}github_username={result.get('github_username')}"
            redirect_url += f"&github_user_id={result.get('github_user_id')}"
            if result.get('temp_data_id'):
                redirect_url += f"&temp_oauth_id={result.get('temp_data_id')}"
        
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except GitHubIntegrationError as e:
        logger.error(f"GitHub OAuth callback failed: {str(e)}")
        # Redirect to error page with details
        error_url = f"/oauth/error?error=callback_failed&description={str(e)}"
        return RedirectResponse(url=error_url, status_code=302)
    except Exception as e:
        logger.error(f"Unexpected error during OAuth callback: {str(e)}")
        error_url = "/oauth/error?error=internal_error&description=An unexpected error occurred"
        return RedirectResponse(url=error_url, status_code=302)


@router.get("/status", response_model=GitHubOAuthStatusResponse)
async def get_github_oauth_status(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get GitHub OAuth integration status for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        GitHubOAuthStatusResponse with integration status
        
    Raises:
        HTTPException: If status check fails
    """
    try:
        oauth_service = GitHubOAuthService()
        
        # Get user's GitHub integration
        integration = await oauth_service.get_user_integration(db=db, user_id=current_user.id)
        
        if integration:
            # Validate token if integration exists
            try:
                token_info = await oauth_service.validate_token(integration.access_token)
                is_valid = token_info.get("valid", False)
            except Exception:
                is_valid = False
            
            return GitHubOAuthStatusResponse(
                connected=True,
                github_username=integration.github_username,
                github_user_id=integration.github_user_id,
                integration_id=integration.id,
                scopes=integration.scope.split(" ") if integration.scope else [],
                connected_at=integration.created_at,
                last_used=integration.last_used,
                token_valid=is_valid
            )
        else:
            return GitHubOAuthStatusResponse(
                connected=False,
                github_username=None,
                github_user_id=None,
                integration_id=None,
                scopes=[],
                connected_at=None,
                last_used=None,
                token_valid=False
            )
            
    except Exception as e:
        logger.error(f"Failed to get GitHub OAuth status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get OAuth status")


@router.get("/integration", response_model=GitHubOAuthIntegrationResponse)
async def get_github_integration(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed GitHub OAuth integration information for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        GitHubOAuthIntegrationResponse with detailed integration info
        
    Raises:
        HTTPException: If integration not found or access fails
    """
    try:
        oauth_service = GitHubOAuthService()
        
        # Get user's GitHub integration
        integration = await oauth_service.get_user_integration(db=db, user_id=current_user.id)
        
        if not integration:
            raise HTTPException(status_code=404, detail="GitHub integration not found")
        
        # Validate token
        try:
            token_info = await oauth_service.validate_token(integration.access_token)
            is_valid = token_info.get("valid", False)
            token_scopes = token_info.get("scopes", [])
        except Exception:
            is_valid = False
            token_scopes = []
        
        return GitHubOAuthIntegrationResponse(
            id=integration.id,
            github_user_id=integration.github_user_id,
            github_username=integration.github_username,
            github_email=integration.github_email,
            github_name=integration.github_name,
            scopes=integration.scope.split(" ") if integration.scope else [],
            token_scopes=token_scopes,
            token_valid=is_valid,
            created_at=integration.created_at,
            updated_at=integration.updated_at,
            last_used=integration.last_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get GitHub integration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get integration details")


@router.delete("/revoke")
async def revoke_github_oauth(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Revoke GitHub OAuth integration for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If revocation fails
    """
    try:
        oauth_service = GitHubOAuthService()
        
        # Revoke integration
        revoked = await oauth_service.revoke_integration(db=db, user_id=current_user.id)
        
        if revoked:
            logger.info(f"GitHub OAuth revoked for user {current_user.id}")
            return {"message": "GitHub integration revoked successfully"}
        else:
            raise HTTPException(status_code=404, detail="No active GitHub integration found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke GitHub OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to revoke integration")


@router.delete("")
async def disconnect_github_oauth(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Disconnect GitHub OAuth integration (alias for revoke).
    Frontend calls DELETE /api/v1/github/oauth
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        oauth_service = GitHubOAuthService()
        revoked = await oauth_service.revoke_integration(db=db, user_id=current_user.id)
        
        if revoked:
            logger.info(f"GitHub OAuth disconnected for user {current_user.id}")
            return {"message": "GitHub integration disconnected successfully"}
        else:
            raise HTTPException(status_code=404, detail="No active GitHub integration found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect GitHub OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to disconnect integration")


@router.post("/validate-token")
async def validate_github_token(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Validate GitHub access token for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Token validation result
        
    Raises:
        HTTPException: If validation fails or integration not found
    """
    try:
        oauth_service = GitHubOAuthService()
        
        # Get user's GitHub integration
        integration = await oauth_service.get_user_integration(db=db, user_id=current_user.id)
        
        if not integration:
            raise HTTPException(status_code=404, detail="GitHub integration not found")
        
        # Validate token
        token_info = await oauth_service.validate_token(integration.access_token)
        
        # Update last_used timestamp if token is valid
        if token_info.get("valid"):
            integration.last_used = datetime.utcnow()
            await db.commit()
        
        return {
            "valid": token_info.get("valid", False),
            "github_user_id": token_info.get("user_id"),
            "github_username": token_info.get("username"),
            "scopes": token_info.get("scopes", []),
            "last_validated": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except GitHubIntegrationError as e:
        logger.error(f"GitHub token validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        raise HTTPException(status_code=500, detail="Token validation failed")


# Admin endpoints for managing OAuth integrations
@router.get("/admin/cleanup-states")
async def cleanup_expired_oauth_states(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Clean up expired OAuth states (admin only).
    
    Args:
        current_user: Current authenticated user (must be admin)
        db: Database session
        
    Returns:
        Cleanup result
        
    Raises:
        HTTPException: If user is not admin or cleanup fails
    """
    # Check if user is admin (assuming there's an is_admin field or role check)
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        oauth_service = GitHubOAuthService()
        
        # Clean up expired states
        cleaned_count = await oauth_service.cleanup_expired_states(db)
        
        logger.info(f"Admin {current_user.id} cleaned up {cleaned_count} expired OAuth states")
        
        return {
            "message": f"Cleaned up {cleaned_count} expired OAuth states",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired OAuth states: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")


@router.post("/associate-temp")
async def associate_temp_oauth_data(
    temp_data_id: str,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Associate temporary OAuth data with current user after login.
    
    Args:
        temp_data_id: Temporary OAuth data ID from callback
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Integration details
        
    Raises:
        HTTPException: If association fails
    """
    try:
        oauth_service = GitHubOAuthService()
        
        # Associate temporary OAuth data with user
        integration = await oauth_service.associate_temp_oauth_with_user(
            db=db,
            user_id=current_user.id,
            temp_data_id=temp_data_id
        )
        
        logger.info(f"Associated temp OAuth data {temp_data_id} with user {current_user.id}")
        
        return {
            "message": "GitHub integration associated successfully",
            "integration_id": integration.id,
            "github_username": integration.github_username,
            "github_user_id": integration.github_user_id,
            "scopes": integration.scope.split(" ") if integration.scope else []
        }
        
    except GitHubIntegrationError as e:
        logger.error(f"Failed to associate temp OAuth data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during OAuth association: {str(e)}")
        raise HTTPException(status_code=500, detail="OAuth association failed")