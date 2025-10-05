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
    RABBITMQ_URL: str = "amqp://codenova:rabbitmq_password@localhost:5672/"
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production-min-32-chars"
    ENVIRONMENT: str = "development"
    
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables like VITE_*

settings = Settings()
