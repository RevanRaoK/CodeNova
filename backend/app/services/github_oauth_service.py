"""
GitHub OAuth Service

This service handles GitHub OAuth authentication flow including state management,
token exchange, and secure token storage with user association.

Requirements covered: 3.1, 3.2
"""

import asyncio
import secrets
import logging
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import GitHubIntegrationError
from app.models.github_oauth import GitHubOAuthIntegration, GitHubOAuthState, GitHubOAuthTempData
from app.models.users import User
from app.services.github_api_client import GitHubAPIClient, create_github_api_client

logger = logging.getLogger(__name__)


class GitHubOAuthService:
    """
    Service for handling GitHub OAuth authentication flow.
    
    Provides methods for:
    - Initiating OAuth flow with state management
    - Handling OAuth callbacks and token exchange
    - Storing and managing user access tokens
    - Validating and refreshing tokens
    
    Requirements covered: 3.1, 3.2
    """
    
    def __init__(self):
        self.client_id = settings.GITHUB_CLIENT_ID
        self.client_secret = settings.GITHUB_CLIENT_SECRET
        self.redirect_uri = settings.GITHUB_OAUTH_REDIRECT_URI
        self.github_api_base = settings.GITHUB_API_BASE_URL
        
        # OAuth scopes for repository access and user information
        self.default_scopes = ["user:email", "repo", "read:org"]
        
        # State expiration time (10 minutes)
        self.state_expiration_minutes = 10
    
    async def initiate_oauth_flow(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        redirect_url: Optional[str] = None,
        scopes: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """
        Initiate GitHub OAuth flow by generating authorization URL and storing state.
        
        Args:
            db: Database session
            user_id: Optional user ID for authenticated flows
            redirect_url: Optional URL to redirect to after OAuth completion
            scopes: Optional custom scopes (defaults to repo access)
            
        Returns:
            Tuple of (authorization_url, state)
            
        Raises:
            GitHubIntegrationError: If OAuth configuration is invalid
        """
        try:
            # Validate OAuth configuration
            if not self.client_id or not self.client_secret:
                raise GitHubIntegrationError(
                    "GitHub OAuth not configured. Missing client ID or secret."
                )
            
            # Generate secure random state
            state = secrets.token_urlsafe(32)
            
            # Use default scopes if none provided
            if scopes is None:
                scopes = self.default_scopes
            
            # Store state in database
            oauth_state = GitHubOAuthState(
                state=state,
                user_id=user_id,
                redirect_url=redirect_url,
                additional_data={"scopes": scopes},
                expires_at=datetime.utcnow() + timedelta(minutes=self.state_expiration_minutes)
            )
            
            db.add(oauth_state)
            await db.commit()
            
            # Build authorization URL
            auth_params = {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "scope": " ".join(scopes),
                "state": state,
                "response_type": "code"
            }
            
            authorization_url = f"https://github.com/login/oauth/authorize?{urlencode(auth_params)}"
            
            logger.info(f"Initiated OAuth flow for user {user_id} with state {state}")
            return authorization_url, state
            
        except Exception as e:
            logger.error(f"Failed to initiate OAuth flow: {str(e)}")
            raise GitHubIntegrationError(f"Failed to initiate OAuth flow: {str(e)}")
    
    async def handle_oauth_callback(
        self,
        db: AsyncSession,
        code: str,
        state: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Handle OAuth callback by exchanging code for access token and storing integration.
        
        Args:
            db: Database session
            code: Authorization code from GitHub
            state: State parameter for CSRF protection
            user_id: Optional user ID (required for authenticated flows)
            
        Returns:
            Dictionary containing integration details and redirect URL
            
        Raises:
            GitHubIntegrationError: If callback handling fails
        """
        try:
            # Validate and retrieve state
            oauth_state = await self._validate_oauth_state(db, state, user_id)
            
            # Exchange code for access token
            token_data = await self._exchange_code_for_token(code)
            
            # Get GitHub user information
            github_user = await self._get_github_user_info(token_data["access_token"])
            
            # Determine user ID (from state or parameter)
            target_user_id = oauth_state.user_id or user_id
            
            if target_user_id:
                # Store integration for authenticated user
                integration = await self._store_oauth_integration(
                    db, target_user_id, token_data, github_user
                )
                
                integration_result = {
                    "integration_id": integration.id,
                    "github_username": integration.github_username,
                    "github_user_id": integration.github_user_id,
                    "redirect_url": oauth_state.redirect_url,
                    "scopes": integration.scope.split(" ") if integration.scope else []
                }
            else:
                # Handle unauthenticated OAuth flow
                # Store temporary OAuth data for later association
                temp_data = GitHubOAuthTempData(
                    github_user_id=github_user["id"],
                    github_username=github_user["login"],
                    github_email=github_user.get("email"),
                    github_name=github_user.get("name"),
                    access_token=token_data["access_token"],
                    token_type=token_data.get("token_type", "bearer"),
                    scope=token_data.get("scope", ""),
                    refresh_token=token_data.get("refresh_token"),
                    expires_at=datetime.utcnow() + timedelta(hours=24)  # Expire in 24 hours
                )
                
                db.add(temp_data)
                await db.commit()
                await db.refresh(temp_data)
                
                integration_result = {
                    "integration_id": None,
                    "github_username": github_user["login"],
                    "github_user_id": github_user["id"],
                    "redirect_url": oauth_state.redirect_url,
                    "scopes": token_data.get("scope", "").split(" ") if token_data.get("scope") else [],
                    "temp_data_id": temp_data.id  # ID for later retrieval
                }
            
            # Clean up state
            await db.delete(oauth_state)
            await db.commit()
            
            logger.info(f"Successfully completed OAuth flow for user {target_user_id or 'unauthenticated'}")
            
            return integration_result
            
        except Exception as e:
            logger.error(f"Failed to handle OAuth callback: {str(e)}")
            raise GitHubIntegrationError(f"OAuth callback failed: {str(e)}")
    
    async def get_user_integration(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[GitHubOAuthIntegration]:
        """
        Get active GitHub OAuth integration for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            GitHubOAuthIntegration if found and active, None otherwise
        """
        try:
            result = await db.execute(
                select(GitHubOAuthIntegration)
                .where(
                    GitHubOAuthIntegration.user_id == user_id,
                    GitHubOAuthIntegration.is_active == True
                )
                .order_by(GitHubOAuthIntegration.created_at.desc())
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get user integration: {str(e)}")
            return None
    
    async def revoke_integration(
        self,
        db: AsyncSession,
        user_id: int,
        integration_id: Optional[str] = None
    ) -> bool:
        """
        Revoke GitHub OAuth integration for a user.
        
        Args:
            db: Database session
            user_id: User ID
            integration_id: Optional specific integration ID to revoke
            
        Returns:
            True if integration was revoked, False otherwise
        """
        try:
            query = select(GitHubOAuthIntegration).where(
                GitHubOAuthIntegration.user_id == user_id,
                GitHubOAuthIntegration.is_active == True
            )
            
            if integration_id:
                query = query.where(GitHubOAuthIntegration.id == integration_id)
            
            result = await db.execute(query)
            integration = result.scalar_one_or_none()
            
            if not integration:
                return False
            
            # Try to revoke token with GitHub
            try:
                await self._revoke_github_token(integration.access_token)
            except Exception as e:
                logger.warning(f"Failed to revoke token with GitHub: {str(e)}")
            
            # Mark integration as inactive
            integration.is_active = False
            integration.updated_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Revoked GitHub integration {integration.id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke integration: {str(e)}")
            return False
    
    async def validate_token(
        self,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Validate GitHub access token and return token information.
        
        Args:
            access_token: GitHub access token
            
        Returns:
            Dictionary containing token validation results
            
        Raises:
            GitHubIntegrationError: If token validation fails
        """
        try:
            # Use the enhanced API client with rate limiting and error handling
            api_client = create_github_api_client(access_token)
            
            try:
                response = await api_client.http_request_with_retry(
                    "GET",
                    f"{self.github_api_base}/user"
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "valid": True,
                        "user_id": user_data.get("id"),
                        "username": user_data.get("login"),
                        "scopes": response.headers.get("X-OAuth-Scopes", "").split(", ")
                    }
                elif response.status_code == 401:
                    return {"valid": False, "error": "Invalid or expired token"}
                else:
                    raise GitHubIntegrationError(f"Token validation failed: {response.status_code}")
            
            finally:
                await api_client.close()
                    
        except GitHubIntegrationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            raise GitHubIntegrationError(f"Token validation error: {str(e)}")
    
    async def _validate_oauth_state(
        self,
        db: AsyncSession,
        state: str,
        user_id: Optional[int] = None
    ) -> GitHubOAuthState:
        """Validate OAuth state parameter and return state object."""
        result = await db.execute(
            select(GitHubOAuthState).where(GitHubOAuthState.state == state)
        )
        oauth_state = result.scalar_one_or_none()
        
        if not oauth_state:
            raise GitHubIntegrationError("Invalid OAuth state parameter")
        
        if oauth_state.is_expired:
            await db.delete(oauth_state)
            await db.commit()
            raise GitHubIntegrationError("OAuth state has expired")
        
        # Validate user ID if provided
        if user_id and oauth_state.user_id and oauth_state.user_id != user_id:
            raise GitHubIntegrationError("OAuth state user mismatch")
        
        return oauth_state
    
    async def _exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        # Use enhanced API client for token exchange with retry logic
        api_client = GitHubAPIClient(enable_rate_limit_handling=True)
        
        try:
            response = await api_client.http_request_with_retry(
                "POST",
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri
                },
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                raise GitHubIntegrationError(f"Token exchange failed: {response.status_code}")
            
            token_data = response.json()
            
            if "error" in token_data:
                raise GitHubIntegrationError(f"Token exchange error: {token_data['error']}")
            
            return token_data
        
        finally:
            await api_client.close()
    
    async def _get_github_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get GitHub user information using access token."""
        api_client = create_github_api_client(access_token)
        
        try:
            response = await api_client.http_request_with_retry(
                "GET",
                f"{self.github_api_base}/user"
            )
            
            if response.status_code != 200:
                raise GitHubIntegrationError(f"Failed to get user info: {response.status_code}")
            
            return response.json()
        
        finally:
            await api_client.close()
    
    async def _store_oauth_integration(
        self,
        db: AsyncSession,
        user_id: int,
        token_data: Dict[str, Any],
        github_user: Dict[str, Any]
    ) -> GitHubOAuthIntegration:
        """Store or update OAuth integration in database."""
        # Check for existing integration
        result = await db.execute(
            select(GitHubOAuthIntegration)
            .where(
                GitHubOAuthIntegration.user_id == user_id,
                GitHubOAuthIntegration.github_user_id == github_user["id"]
            )
        )
        existing_integration = result.scalar_one_or_none()
        
        if existing_integration:
            # Update existing integration
            existing_integration.access_token = token_data["access_token"]
            existing_integration.token_type = token_data.get("token_type", "bearer")
            existing_integration.scope = token_data.get("scope", "")
            existing_integration.refresh_token = token_data.get("refresh_token")
            existing_integration.github_username = github_user["login"]
            existing_integration.github_email = github_user.get("email")
            existing_integration.github_name = github_user.get("name")
            existing_integration.is_active = True
            existing_integration.updated_at = datetime.utcnow()
            
            integration = existing_integration
        else:
            # Create new integration
            integration = GitHubOAuthIntegration(
                user_id=user_id,
                github_user_id=github_user["id"],
                github_username=github_user["login"],
                github_email=github_user.get("email"),
                github_name=github_user.get("name"),
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "bearer"),
                scope=token_data.get("scope", ""),
                refresh_token=token_data.get("refresh_token"),
                is_active=True
            )
            db.add(integration)
        
        await db.commit()
        await db.refresh(integration)
        
        return integration
    
    async def _revoke_github_token(self, access_token: str) -> None:
        """Revoke access token with GitHub."""
        api_client = GitHubAPIClient(enable_rate_limit_handling=True)
        
        try:
            await api_client.http_request_with_retry(
                "DELETE",
                f"{self.github_api_base}/applications/{self.client_id}/token",
                auth=(self.client_id, self.client_secret),
                json={"access_token": access_token}
            )
        finally:
            await api_client.close()
    
    async def associate_temp_oauth_with_user(
        self,
        db: AsyncSession,
        user_id: int,
        temp_data_id: str
    ) -> GitHubOAuthIntegration:
        """
        Associate temporary OAuth data with a user after they log in.
        
        Args:
            db: Database session
            user_id: User ID to associate with
            temp_data_id: Temporary OAuth data ID
            
        Returns:
            GitHubOAuthIntegration object
            
        Raises:
            GitHubIntegrationError: If association fails
        """
        try:
            # Retrieve temporary OAuth data
            result = await db.execute(
                select(GitHubOAuthTempData).where(GitHubOAuthTempData.id == temp_data_id)
            )
            temp_data = result.scalar_one_or_none()
            
            if not temp_data:
                raise GitHubIntegrationError("Temporary OAuth data not found or expired")
            
            if temp_data.is_expired:
                await db.delete(temp_data)
                await db.commit()
                raise GitHubIntegrationError("Temporary OAuth data has expired")
            
            # Create integration from temporary data
            token_data = {
                "access_token": temp_data.access_token,
                "token_type": temp_data.token_type,
                "scope": temp_data.scope,
                "refresh_token": temp_data.refresh_token
            }
            
            github_user = {
                "id": temp_data.github_user_id,
                "login": temp_data.github_username,
                "email": temp_data.github_email,
                "name": temp_data.github_name
            }
            
            integration = await self._store_oauth_integration(
                db, user_id, token_data, github_user
            )
            
            # Clean up temporary data
            await db.delete(temp_data)
            await db.commit()
            
            logger.info(f"Associated GitHub OAuth with user {user_id}")
            return integration
            
        except Exception as e:
            logger.error(f"Failed to associate OAuth with user: {str(e)}")
            raise GitHubIntegrationError(f"OAuth association failed: {str(e)}")
    
    async def get_temp_oauth_data(
        self,
        db: AsyncSession,
        github_username: str
    ) -> Optional[GitHubOAuthTempData]:
        """
        Get temporary OAuth data by GitHub username.
        
        Args:
            db: Database session
            github_username: GitHub username
            
        Returns:
            GitHubOAuthTempData if found and not expired, None otherwise
        """
        try:
            result = await db.execute(
                select(GitHubOAuthTempData)
                .where(GitHubOAuthTempData.github_username == github_username)
                .order_by(GitHubOAuthTempData.created_at.desc())
            )
            temp_data = result.scalar_one_or_none()
            
            if temp_data and not temp_data.is_expired:
                return temp_data
            elif temp_data and temp_data.is_expired:
                # Clean up expired data
                await db.delete(temp_data)
                await db.commit()
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get temp OAuth data: {str(e)}")
            return None
    
    async def cleanup_expired_states(self, db: AsyncSession) -> int:
        """
        Clean up expired OAuth states from database.
        
        Args:
            db: Database session
            
        Returns:
            Number of expired states cleaned up
        """
        try:
            result = await db.execute(
                select(GitHubOAuthState)
                .where(GitHubOAuthState.expires_at < datetime.utcnow())
            )
            expired_states = result.scalars().all()
            
            if expired_states:
                for state in expired_states:
                    await db.delete(state)
                await db.commit()
                
                logger.info(f"Cleaned up {len(expired_states)} expired OAuth states")
            
            return len(expired_states)
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired states: {str(e)}")
            return 0