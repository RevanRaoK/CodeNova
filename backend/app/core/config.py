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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
