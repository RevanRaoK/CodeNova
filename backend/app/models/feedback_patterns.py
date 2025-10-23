"""
Feedback pattern models for personalized AI learning.

This module contains the database model for caching user feedback patterns
to enable efficient personalized AI suggestions.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime


class UserFeedbackPattern(Base):
    """
    UserFeedbackPattern model for caching aggregated feedback patterns per user.
    
    This table stores pre-calculated statistics about user feedback patterns
    to optimize personalized AI suggestion generation without expensive
    real-time aggregations.
    
    Requirements covered: 8.1, 8.2, 8.9
    """
    __tablename__ = "user_feedback_patterns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    acceptance_rate = Column(Float, nullable=False, default=0.0)
    total_feedback_count = Column(Integer, nullable=False, default=0)
    accepted_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", backref="feedback_patterns")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_feedback_patterns_user', 'user_id'),
        Index('idx_user_feedback_patterns_category', 'category'),
        Index('idx_user_feedback_patterns_severity', 'severity'),
        Index('idx_user_feedback_patterns_user_category', 'user_id', 'category'),
        Index('idx_user_feedback_patterns_acceptance', 'acceptance_rate'),
        Index('idx_user_feedback_patterns_updated', 'last_updated'),
    )

    def __repr__(self):
        return (f"<UserFeedbackPattern(user_id={self.user_id}, category={self.category}, "
                f"severity={self.severity}, acceptance_rate={self.acceptance_rate:.2f})>")

    @property
    def is_mostly_accepted(self) -> bool:
        """Check if this pattern is mostly accepted by the user."""
        return self.acceptance_rate >= 0.7

    @property
    def is_mostly_rejected(self) -> bool:
        """Check if this pattern is mostly rejected by the user."""
        return self.acceptance_rate <= 0.3

    def get_pattern_summary(self) -> dict:
        """Get a summary of this feedback pattern."""
        return {
            'category': self.category,
            'severity': self.severity,
            'acceptance_rate': round(self.acceptance_rate, 2),
            'total_feedback': self.total_feedback_count,
            'accepted': self.accepted_count,
            'rejected': self.rejected_count,
            'preference': 'accepts' if self.is_mostly_accepted else 'rejects' if self.is_mostly_rejected else 'neutral'
        }
