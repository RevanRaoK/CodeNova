from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeNova Intelligent Code Review Bot"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: AnyUrl
    GEMINI_API_KEY: str = ""  # Made optional with empty string as default
    GEMINI_MODEL: str = "models/gemini-1.5-flash"  # Default model, can be overridden in .env

    # Add these fields because they appear in your env
    REDIS_URL: str
    RABBITMQ_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"  # Example default value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
