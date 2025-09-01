from sqlalchemy import (Column, Integer, String, Text, DateTime, ForeignKey, create_engine, Enum)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class User(Base):
  __tablename__="users"
  id= Column(Integer, primary_key=True, index=True)
  username=Column(String, unique=True, index=True, nullable=False)
  email = Column(String, unique=True, index=True, nullable=False)
  hashed_password = Column(String, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)
  repositories = relationship("Repository", back_populates="owner")

class Repository(Base):
    __tablename__ = "repositories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    url = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner = relationship("User", back_populates="repositories")
    reviews = relationship("Review", back_populates="repository")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    commit_hash = Column(String, nullable=False)
    status = Column(String, default="pending") # pending, in_progress, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    repository = relationship("Repository", back_populates="reviews")
    suggestions = relationship("ReviewSuggestion", back_populates="review")

class SeverityLevel(enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    SUGGESTION = "suggestion"

class ReviewSuggestion(Base):
    __tablename__ = "review_suggestions"
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"))
    file_path = Column(String, nullable=False)
    line_number = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    # Enum backed by PostgreSQL type `severity_level`
    severity = Column(Enum(SeverityLevel, name="severity_level"), nullable=False)
    review = relationship("Review", back_populates="suggestions")
    feedback = relationship("Feedback", back_populates="suggestion", uselist=False)

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    suggestion_id = Column(Integer, ForeignKey("review_suggestions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, nullable=False) # 'accepted', 'rejected', 'modified'
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    suggestion = relationship("ReviewSuggestion", back_populates="feedback")
