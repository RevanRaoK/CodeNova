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
    
    @validator('firstName', 'lastName')
    def validate_names(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Name cannot be empty')
            if len(v) > 100:
                raise ValueError('Name cannot exceed 100 characters')
            if not v.replace(' ', '').replace('-', '').replace("'", '').isalpha():
                raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip() if v else v
    
    @validator('jobTitle')
    def validate_job_title(cls, v):
        if v is not None:
            if len(v.strip()) > 200:
                raise ValueError('Job title cannot exceed 200 characters')
        return v.strip() if v else v
    
    @validator('bio')
    def validate_bio(cls, v):
        if v is not None:
            if len(v.strip()) > 1000:
                raise ValueError('Bio cannot exceed 1000 characters')
        return v.strip() if v else v
    
    @validator('programmingLanguages')
    def validate_programming_languages(cls, v):
        if v is not None:
            if len(v) > 20:
                raise ValueError('Cannot specify more than 20 programming languages')
            # Remove duplicates and empty strings
            v = list(set([lang.strip() for lang in v if lang.strip()]))
        return v

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
    
    @validator('theme')
    def validate_theme(cls, v):
        allowed_themes = ['light', 'dark', 'auto']
        if v not in allowed_themes:
            raise ValueError(f'Theme must be one of: {", ".join(allowed_themes)}')
        return v
    
    @validator('language')
    def validate_language(cls, v):
        allowed_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko']
        if v not in allowed_languages:
            raise ValueError(f'Language must be one of: {", ".join(allowed_languages)}')
        return v
    
    @validator('defaultProgrammingLanguage')
    def validate_programming_language(cls, v):
        allowed_languages = [
            'javascript', 'python', 'java', 'typescript', 'c++', 'c#', 'c',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'r',
            'matlab', 'perl', 'shell', 'sql', 'html', 'css'
        ]
        if v not in allowed_languages:
            raise ValueError(f'Programming language must be one of: {", ".join(allowed_languages)}')
        return v
    
    @validator('aiModel')
    def validate_ai_model(cls, v):
        allowed_models = ['gemini-pro', 'gpt-4', 'gpt-3.5-turbo', 'claude-3', 'llama-2']
        if v not in allowed_models:
            raise ValueError(f'AI model must be one of: {", ".join(allowed_models)}')
        return v
    
    @validator('codeEditorTheme')
    def validate_editor_theme(cls, v):
        allowed_themes = [
            'vs-light', 'vs-dark', 'hc-black', 'monokai', 'solarized-light',
            'solarized-dark', 'github-light', 'github-dark', 'dracula'
        ]
        if v not in allowed_themes:
            raise ValueError(f'Code editor theme must be one of: {", ".join(allowed_themes)}')
        return v

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

class ThemePreference(BaseModel):
    theme: str
    
    @validator('theme')
    def validate_theme(cls, v):
        allowed_themes = ['light', 'dark', 'auto']
        if v not in allowed_themes:
            raise ValueError(f'Theme must be one of: {", ".join(allowed_themes)}')
        return v