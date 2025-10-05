from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
import datetime
from enum import Enum as PyEnum
import uuid

from app.core.database import Base

class UserRole(str, PyEnum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    GUEST = "guest"
    USER = "user"
    TEAM_LEAD = "team_lead"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)  # Make nullable for OAuth users
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Enhanced user management fields
    team_id = Column(String(36), nullable=True, index=True)  # Will add FK constraint in migration
    preferences = Column(JSON, default=dict, nullable=False)
    
    # Profile fields
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    job_title = Column(String(200), nullable=True)
    bio = Column(String(1000), nullable=True)
    programming_languages = Column(String(500), nullable=True)  # JSON string of languages
    
    # OAuth fields
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'github', etc.
    oauth_id = Column(String(255), nullable=True)  # Provider-specific user ID
    oauth_email_verified = Column(Boolean, default=False)
    profile_picture_url = Column(String(512), nullable=True)
    
    # Timestamps
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    repositories = relationship("Repository", back_populates="user")
    tokens = relationship("Token", back_populates="user")
    direct_analyses = relationship("DirectAnalysis", back_populates="user")
    feedback_records = relationship("FeedbackRecord", back_populates="user")


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="tokens")