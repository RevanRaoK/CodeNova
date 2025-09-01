# app/schemas/repository.py

from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class RepositoryBase(BaseModel):
    url: HttpUrl
    name: str
    description: Optional[str] = None

class RepositoryCreate(RepositoryBase):
    user_id: int

class RepositoryUpdate(BaseModel):
    description: Optional[str] = None

class RepositoryRead(RepositoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Updated for Pydantic v2
