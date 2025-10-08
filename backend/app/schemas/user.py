from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.models.users import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    pass

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

class UserRoleUpdate(BaseModel):
    role: UserRole

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
    jobTitle: Optional[str] = None
    bio: Optional[str] = None
    programmingLanguages: Optional[List[str]] = None
    profilePictureUrl: Optional[str] = None

class NotificationPreferences(BaseModel):
    email_notifications: bool = True
    push_notifications: bool = True
    analysis_complete: bool = True
    new_issues: bool = True
    team_updates: bool = True
    security_alerts: bool = True

    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str

    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class UserPreferences(BaseModel):
    theme: Optional[str] = "light"
    language: Optional[str] = "en"
    timezone: Optional[str] = "UTC"
    defaultProgrammingLanguage: Optional[str] = "javascript"
    aiModel: Optional[str] = "gemini-pro"
    codeEditorTheme: Optional[str] = "vs-light"
    autoSave: Optional[bool] = True
    showLineNumbers: Optional[bool] = True
