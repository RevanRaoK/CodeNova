"""
GitHub OAuth Integration Models

Models for storing GitHub OAuth tokens and user associations.
Supports secure token storage and user-repository access management.

Requirements covered: 3.1, 3.2
"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean, Integer, Text
from sqlalchemy.orm import relationship
import datetime
import uuid

from app.core.database import Base


class GitHubOAuthIntegration(Base):
    """
    GitHub OAuth integration model for storing user access tokens and GitHub profile information.
    
    Requirements covered: 3.1, 3.2
    """
    __tablename__ = "github_oauth_integrations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # GitHub user information
    github_user_id = Column(Integer, nullable=False, index=True)
    github_username = Column(String(255), nullable=False, index=True)
    github_email = Column(String(255), nullable=True)
    github_name = Column(String(255), nullable=True)
    
    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=False)  # GitHub access token
    token_type = Column(String(50), default="bearer", nullable=False)
    scope = Column(String(500), nullable=True)  # Granted scopes
    
    # Token metadata
    token_expires_at = Column(DateTime, nullable=True)  # If GitHub provides expiration
    refresh_token = Column(Text, nullable=True)  # If available
    
    # Integration status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_used = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="github_oauth_integrations")

    def __repr__(self):
        return f"<GitHubOAuthIntegration(id={self.id}, user_id={self.user_id}, github_username={self.github_username})>"


class GitHubOAuthState(Base):
    """
    Temporary storage for OAuth state parameters to prevent CSRF attacks.
    
    Requirements covered: 3.1
    """
    __tablename__ = "github_oauth_states"

    state = Column(String(255), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Optional for anonymous flows
    
    # State metadata
    redirect_url = Column(String(1000), nullable=True)  # Where to redirect after OAuth
    additional_data = Column(JSON, default=dict, nullable=False)  # Extra state data
    
    # Expiration
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    def __repr__(self):
        return f"<GitHubOAuthState(state={self.state}, user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_expired(self) -> bool:
        """Check if the OAuth state has expired."""
        return datetime.datetime.utcnow() > self.expires_at


class GitHubOAuthTempData(Base):
    """
    Temporary storage for OAuth data from unauthenticated users.
    
    This stores OAuth tokens temporarily until the user logs in or registers.
    """
    __tablename__ = "github_oauth_temp_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # GitHub user information
    github_user_id = Column(Integer, nullable=False, index=True)
    github_username = Column(String(255), nullable=False, index=True)
    github_email = Column(String(255), nullable=True)
    github_name = Column(String(255), nullable=True)
    
    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=False)
    token_type = Column(String(50), default="bearer", nullable=False)
    scope = Column(String(500), nullable=True)
    refresh_token = Column(Text, nullable=True)
    
    # Expiration (tokens expire after 24 hours if not claimed)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    def __repr__(self):
        return f"<GitHubOAuthTempData(id={self.id}, github_username={self.github_username})>"

    @property
    def is_expired(self) -> bool:
        """Check if the temp OAuth data has expired."""
        return datetime.datetime.utcnow() > self.expires_at