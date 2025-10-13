from sqlalchemy import Column, String, DateTime, BigInteger, ForeignKey, Boolean, Integer, Integer
from sqlalchemy.orm import relationship
import datetime
import uuid

from app.core.database import Base


class StoredFile(Base):
    """
    File storage model for Digital Ocean Spaces integration.
    
    Requirements covered: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    __tablename__ = "stored_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)  # Original uploaded filename
    file_path = Column(String(512), nullable=False)  # Path in Digital Ocean Spaces
    file_size = Column(BigInteger, nullable=False)  # File size in bytes
    content_type = Column(String(100), nullable=False, index=True)  # MIME type
    
    # Digital Ocean Spaces metadata
    spaces_url = Column(String(512), nullable=False)  # Full URL to file in Spaces
    spaces_key = Column(String(512), nullable=False)  # Object key in Spaces
    bucket_name = Column(String(100), nullable=False)  # Spaces bucket name
    
    # File metadata and security
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for integrity
    is_public = Column(Boolean, default=False, nullable=False)  # Public access flag
    access_permissions = Column(String(500), nullable=True)  # JSON string of access permissions
    
    # Batch upload metadata
    batch_id = Column(String(36), nullable=True, index=True)  # For grouping multiple uploads
    upload_metadata = Column(String(2000), nullable=True)  # JSON string for additional metadata
    processing_status = Column(String(20), default="completed", nullable=False, index=True)  # PENDING, PROCESSING, COMPLETED, FAILED
    
    # Analysis metadata
    is_analyzed = Column(Boolean, default=False, nullable=False, index=True)
    analysis_id = Column(String(36), nullable=True, index=True)  # Link to analysis result
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    last_accessed = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration date
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<StoredFile(id={self.id}, filename={self.filename}, user_id={self.user_id}, file_size={self.file_size})>"