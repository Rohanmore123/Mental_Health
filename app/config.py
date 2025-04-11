import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Prasha Healthcare API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Database settings
    # Local database URL
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:Raje%4012345@localhost:5432/Prasha_care")

    # AWS Database settings
    AWS_DB_USERNAME: str = os.getenv("AWS_DB_USERNAME", "postgres")
    AWS_DB_PASSWORD: str = os.getenv("AWS_DB_PASSWORD", "Prashaind2025")
    AWS_DB_HOST: str = os.getenv("AWS_DB_HOST", "localhost")
    AWS_DB_NAME: str = os.getenv("AWS_DB_NAME", "Prasha_care")

    # Construct database URL from AWS settings
    DATABASE_URL: str = f"postgresql://{AWS_DB_USERNAME}:{AWS_DB_PASSWORD}@{AWS_DB_HOST}:5432/{AWS_DB_NAME}"

    # JWT Authentication settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "prasha_healthcare_secret_key_for_jwt_tokens_2025")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # OpenAI settings for AI chat
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # AWS settings
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()
