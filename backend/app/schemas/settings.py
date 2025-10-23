"""
Settings schemas for comprehensive user settings management.
"""

from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from enum import Enum


class ThemeType(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class LanguageType(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    RU = "ru"
    ZH = "zh"
    JA = "ja"
    KO = "ko"


class AIModelType(str, Enum):
    GEMINI_PRO = "gemini-pro"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"


class EditorThemeType(str, Enum):
    VS_LIGHT = "vs-light"
    VS_DARK = "vs-dark"
    HC_BLACK = "hc-black"
    HC_LIGHT = "hc-light"
    MONOKAI = "monokai"
    SOLARIZED_LIGHT = "solarized-light"
    SOLARIZED_DARK = "solarized-dark"
    GITHUB_LIGHT = "github-light"
    GITHUB_DARK = "github-dark"
    DRACULA = "dracula"


class NotificationFrequency(str, Enum):
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"


class SessionTimeout(int, Enum):
    FIFTEEN_MIN = 15
    THIRTY_MIN = 30
    ONE_HOUR = 60
    TWO_HOURS = 120
    FOUR_HOURS = 240
    EIGHT_HOURS = 480


class GeneralSettings(BaseModel):
    """General application settings."""
    theme: ThemeType = ThemeType.LIGHT
    language: LanguageType = LanguageType.EN
    timezone: str = "UTC"
    defaultProgrammingLanguage: str = "javascript"
    aiModel: AIModelType = AIModelType.GEMINI_PRO
    codeEditorTheme: EditorThemeType = EditorThemeType.VS_LIGHT
    autoSave: bool = True
    showLineNumbers: bool = True
    
    @validator('timezone')
    def validate_timezone(cls, v):
        # Basic timezone validation - in production, use pytz or similar
        if len(v) > 50:
            raise ValueError('Timezone must be 50 characters or less')
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


class EmailNotificationSettings(BaseModel):
    """Email notification preferences."""
    reviewCompleted: bool = True
    newPattern: bool = True
    securityAlert: bool = True
    weeklyDigest: bool = False
    marketingEmails: bool = False


class PushNotificationSettings(BaseModel):
    """Push notification preferences."""
    reviewCompleted: bool = True
    newPattern: bool = False
    securityAlert: bool = True


class NotificationSettings(BaseModel):
    """Notification preferences."""
    emailNotifications: EmailNotificationSettings = EmailNotificationSettings()
    pushNotifications: PushNotificationSettings = PushNotificationSettings()
    frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE


class SecuritySettings(BaseModel):
    """Security settings."""
    twoFactorEnabled: bool = False
    dataCollection: bool = True
    sessionTimeout: SessionTimeout = SessionTimeout.THIRTY_MIN


class IntegrationSettings(BaseModel):
    """Integration settings for external services."""
    githubConnected: bool = False
    gitlabConnected: bool = False
    slackConnected: bool = False
    discordConnected: bool = False
    
    # Integration-specific settings
    githubWebhooksEnabled: bool = False
    autoSyncRepositories: bool = True
    notifyOnPullRequests: bool = True


class TeamSettings(BaseModel):
    """Team management settings."""
    teamId: Optional[str] = None
    teamRole: str = "member"  # member, lead, admin
    allowTeamInvitations: bool = True
    shareAnalyticsWithTeam: bool = False
    autoJoinTeamProjects: bool = True


class APIAccessSettings(BaseModel):
    """API access settings."""
    hasPersonalApiKey: bool = False
    apiKeyPreview: Optional[str] = None
    usePersonalApiKey: bool = False
    apiRateLimit: int = 1000  # requests per hour
    allowApiKeySharing: bool = False


class ComprehensiveSettings(BaseModel):
    """Complete user settings model."""
    general: GeneralSettings = GeneralSettings()
    notifications: NotificationSettings = NotificationSettings()
    security: SecuritySettings = SecuritySettings()
    integrations: IntegrationSettings = IntegrationSettings()
    team: TeamSettings = TeamSettings()
    apiAccess: APIAccessSettings = APIAccessSettings()
    
    class Config:
        from_attributes = True


class SettingsUpdateRequest(BaseModel):
    """Request model for updating settings."""
    general: Optional[GeneralSettings] = None
    notifications: Optional[NotificationSettings] = None
    security: Optional[SecuritySettings] = None
    integrations: Optional[IntegrationSettings] = None
    team: Optional[TeamSettings] = None
    apiAccess: Optional[APIAccessSettings] = None


class SettingsUpdateResponse(BaseModel):
    """Response model for settings updates."""
    settings: ComprehensiveSettings
    message: str = "Settings updated successfully"
    updatedFields: List[str] = []
    timestamp: str
    
    class Config:
        from_attributes = True


class SettingsValidationError(BaseModel):
    """Settings validation error model."""
    field: str
    message: str
    value: Any


class SettingsErrorResponse(BaseModel):
    """Error response for settings operations."""
    error: str
    details: List[SettingsValidationError] = []
    timestamp: str