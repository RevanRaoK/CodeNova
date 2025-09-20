from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from enum import Enum as PyEnum

from app.core.database import Base

class UserRole(str, PyEnum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    GUEST = "guest"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.GUEST, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    repositories = relationship("Repository", back_populates="user")
    tokens = relationship("Token", back_populates="user")


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="tokens")