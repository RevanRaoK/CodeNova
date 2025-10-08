from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeNova Intelligent Code Review Bot"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "postgresql://postgres:codenova_secure_password@localhost:5432/codenova_db"
    GEMINI_API_KEY: str = ""  # Made optional with empty string as default
    GEMINI_MODEL: str = "models/gemini-1.5-flash"  # Default model, can be overridden in .env

    # Add these fields with defaults
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    RABBITMQ_URL: str = "amqp://codenova:rabbitmq_password@localhost:5672/"
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production-min-32-chars"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    TESTING: bool = False
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    # GitHub Integration Configuration
    GITHUB_APP_ID: str = ""
    GITHUB_PRIVATE_KEY: str = ""
    GITHUB_PRIVATE_KEY_PATH: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/github/oauth/callback"
    GITHUB_API_BASE_URL: str = "https://api.github.com"
    GITHUB_WEBHOOK_BASE_URL: str = "http://localhost:8000/api/v1/github"
    
    # Digital Ocean Spaces Configuration
    DO_SPACES_KEY: str = ""
    DO_SPACES_SECRET: str = ""
    DO_SPACES_BUCKET: str = ""
    DO_SPACES_REGION: str = "nyc3"
    DO_SPACES_ENDPOINT: str = ""
    DO_SPACES_CDN_ENDPOINT: str = ""
    
    # File Storage Settings
    MAX_FILE_SIZE_MB: int = 50
    FILE_UPLOAD_PATH: str = "uploads/"
    SIGNED_URL_EXPIRATION_HOURS: int = 24
    ALLOWED_FILE_EXTENSIONS: str = "pdf,doc,docx,txt,jpg,jpeg,png,gif,zip,csv,xlsx,xls,ppt,pptx"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables like VITE_*

settings = Settings()
