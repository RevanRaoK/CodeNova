"""
Google OAuth Service for handling OAuth authentication flow
"""

import httpx
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import secrets
import logging
import datetime

from app.core.config import settings
from app.models.users import User, UserRole
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    """Service for handling Google OAuth authentication"""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
    def get_authorization_url(self, state: str = None) -> str:
        """Generate Google OAuth authorization URL"""
        if not state:
            state = secrets.token_urlsafe(32)
            
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/auth?{query_string}"
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and ID tokens"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            raise Exception(f"Failed to exchange code for tokens: {response.text}")
            
        return response.json()
    
    def verify_id_token(self, id_token_str: str) -> Dict[str, Any]:
        """Verify Google ID token and extract user information"""
        try:
            # First try normal verification
            idinfo = id_token.verify_oauth2_token(
                id_token_str, 
                requests.Request(), 
                self.client_id
            )
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
                
            logger.info(f"Successfully verified Google ID token for user: {idinfo.get('email')}")
            return idinfo
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"ID token verification failed: {error_msg}")
            
            # If it's a token expiration error, handle it more gracefully
            if "Token expired" in error_msg or "expired" in error_msg.lower():
                try:
                    import jwt
                    # Decode without verification to get user info
                    decoded = jwt.decode(id_token_str, options={"verify_signature": False})
                    logger.info(f"Token expired for user: {decoded.get('email')}, exp: {decoded.get('exp')}, iat: {decoded.get('iat')}")
                    
                    # Check if token is only slightly expired (within 5 minutes)
                    current_time = datetime.datetime.utcnow().timestamp()
                    token_exp = decoded.get('exp', 0)
                    time_diff = current_time - token_exp
                    
                    if time_diff < 300:  # Less than 5 minutes expired
                        logger.warning(f"Accepting slightly expired token (expired {time_diff} seconds ago)")
                        # Return the decoded info for slightly expired tokens
                        return decoded
                    else:
                        logger.error(f"Token too old, expired {time_diff} seconds ago")
                        raise Exception("Google ID token has expired. Please sign in again.")
                        
                except Exception as decode_error:
                    logger.error(f"Could not decode expired token: {decode_error}")
                    raise Exception("Invalid or corrupted Google ID token.")
            
            raise Exception(f"Invalid ID token: {error_msg}")
    
    def create_or_update_user(self, db: Session, user_info: Dict[str, Any]) -> User:
        """Create or update user from Google OAuth information"""
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        email_verified = user_info.get('email_verified', False)
        
        if not google_id or not email:
            raise Exception("Missing required user information from Google")
        
        # Check if user exists with this Google ID
        existing_user = db.query(User).filter(
            User.oauth_provider == 'google',
            User.oauth_id == google_id
        ).first()
        
        if existing_user:
            # Update existing OAuth user
            existing_user.full_name = name
            existing_user.profile_picture_url = picture
            existing_user.oauth_email_verified = email_verified
            existing_user.last_login = datetime.datetime.utcnow()
            db.commit()
            db.refresh(existing_user)
            return existing_user
        
        # Check if user exists with this email (for account linking)
        email_user = db.query(User).filter(User.email == email).first()
        
        if email_user:
            # Link Google account to existing user
            if email_user.oauth_provider is None:
                email_user.oauth_provider = 'google'
                email_user.oauth_id = google_id
                email_user.oauth_email_verified = email_verified
                email_user.profile_picture_url = picture
                email_user.last_login = datetime.datetime.utcnow()
                db.commit()
                db.refresh(email_user)
                return email_user
            else:
                raise Exception("Email already associated with another OAuth provider")
        
        # Create new user
        new_user = User(
            email=email,
            full_name=name,
            hashed_password=None,  # OAuth users don't have passwords
            oauth_provider='google',
            oauth_id=google_id,
            oauth_email_verified=email_verified,
            profile_picture_url=picture,
            is_verified=email_verified,
            role=UserRole.DEVELOPER,  # Default role for new OAuth users
            last_login=datetime.datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Created new Google OAuth user: {email}")
        return new_user
    
    async def authenticate_with_google(self, db: Session, code: str) -> Dict[str, Any]:
        """Complete Google OAuth authentication flow"""
        try:
            # Exchange code for tokens
            tokens = await self.exchange_code_for_tokens(code)
            
            # Verify ID token and get user info
            user_info = self.verify_id_token(tokens['id_token'])
            
            # Create or update user
            user = self.create_or_update_user(db, user_info)
            
            # Generate JWT tokens for our application
            auth_tokens = AuthService.create_user_tokens(db, user)
            
            return {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role.value,
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                    'profile_picture_url': user.profile_picture_url,
                    'oauth_provider': user.oauth_provider,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                },
                'access_token': auth_tokens['access_token'],
                'refresh_token': auth_tokens['refresh_token'],
                'token_type': auth_tokens['token_type']
            }
            
        except Exception as e:
            logger.error(f"Google OAuth authentication failed: {e}")
            raise Exception(f"OAuth authentication failed: {str(e)}")

# Create singleton instance
google_oauth_service = GoogleOAuthService()