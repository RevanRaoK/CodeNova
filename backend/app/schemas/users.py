from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserProfile(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: EmailStr
    jobTitle: Optional[str] = None
    bio: Optional[str] = None
    programmingLanguages: List[str] = []
    profilePictureUrl: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    jobTitle: Optional[str] = None
    bio: Optional[str] = None
    programmingLanguages: Optional[List[str]] = None

class NotificationPreferences(BaseModel):
    emailNotifications: Dict[str, bool] = {
        "reviewCompleted": True,
        "newPattern": True,
        "securityAlert": True,
        "weeklyDigest": False,
        "marketingEmails": False
    }
    pushNotifications: Dict[str, bool] = {
        "reviewCompleted": True,
        "newPattern": False,
        "securityAlert": True
    }
    frequency: str = "immediate"  # immediate, daily, weekly

class UserPreferences(BaseModel):
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    defaultProgrammingLanguage: str = "javascript"
    aiModel: str = "gemini-pro"
    codeEditorTheme: str = "vs-light"
    autoSave: bool = True
    showLineNumbers: bool = True

class PasswordChange(BaseModel):
    currentPassword: str
    newPassword: str
    
    @validator('newPassword')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserInDB(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class User(UserInDB):
    pass