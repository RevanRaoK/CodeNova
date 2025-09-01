from backend.app.schemas import repository
from pydantic import BaseModel
from typing import List
from datetime import datetime
from enum import Enum

class SeverityLevel(str, Enum):
  INFO = "info"
  LOW = "low"
  MEDIUM = "medium"
  HIGH = "high"
  CRITICAL = "critical"
  SUGGESTION = "suggestion"

class ReviewSuggestionsBase(BaseModel):
  #Base schema for a single review suggestion
  file_path: str
  line_number: int
  comment: str
  severity: SeverityLevel

class ReviewSuggestionsCreate(ReviewSuggestionsBase):
  #Schema for creating new review suggestion
  pass

class ReviewSuggestionsRead(ReviewSuggestionsBase):
  #Schema for reading a new review suggestion
  id: int

  class Config:
    orm_mode = True

class ReviewBase(BaseModel):
  repository_id: int
  commit_hash: str
  status: str

class ReviewCreate(ReviewBase):
  #Schema to create a new review
  pass

class ReviewRead(ReviewBase):
  #Schema to read a review including suggestions
  id: int
  suggestions: List[ReviewSuggestionsRead] = []
  created_at: datetime

  class Config:
    orm_mode = True