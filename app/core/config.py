from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/venus_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = ""
    MAX_PHOTO_SIZE_MB: int = 10
    
    # Firebase
    FIREBASE_SERVICE_ACCOUNT_PATH: str = ""
    
    # Safaricom Daraja M-Pesa
    DARAJA_CREDENTIALS_URL: str = ""
    CONSUMER_KEY: str = ""
    CONSUMER_SECRET: str = ""
    DARAJA_STK_PUSH_URL: str = ""
    SHORT_CODE: str = ""
    DARAJA_PASSKEY: str = ""
    DARAJA_CALLBACK_URL: str = ""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables (like POSTGRES_USER, POSTGRES_PASSWORD, etc.)
    )


settings = Settings()
