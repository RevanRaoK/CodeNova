from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
import datetime
import uuid

from app.core.database import Base


class Team(Base):
    """
    Team model for organizing users into teams with admin management.
    
    Requirements covered: 3.2, 3.5
    """
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=False, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    settings = Column(JSON, default=dict, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    admin = relationship("User", foreign_keys=[admin_id], lazy="select")

    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name}, admin_id={self.admin_id})>"