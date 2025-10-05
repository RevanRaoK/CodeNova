from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
import datetime
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class FeedbackAction(str, PyEnum):
    ACCEPT = "accept"
    REJECT = "reject"


class EnhancedFeedback(Base):
    """
    Enhanced feedback model for AI suggestions with detailed rejection reasons.
    
    Requirements covered: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    __tablename__ = "enhanced_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    suggestion_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(Enum(FeedbackAction), nullable=False, index=True)
    rejection_reasons = Column(JSON, nullable=True)  # List of predefined reasons
    custom_reason = Column(String(1000), nullable=True)  # Custom reason text
    
    # Additional metadata
    suggestion_type = Column(String(100), nullable=True, index=True)  # Type of AI suggestion
    confidence_score = Column(String(20), nullable=True)  # AI confidence level
    context_data = Column(JSON, nullable=True)  # Additional context about the suggestion
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<EnhancedFeedback(id={self.id}, user_id={self.user_id}, action={self.action}, suggestion_id={self.suggestion_id})>"