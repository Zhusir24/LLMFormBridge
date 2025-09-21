from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    app_name: str = "LLMFormBridge"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./llmbridge.db"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Encryption for API keys
    encryption_key: Optional[str] = None

    # CORS
    allowed_origins: list = ["http://localhost:3000", "http://localhost:5173"]

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Rate limiting
    rate_limit_per_minute: int = 100

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Generate encryption key if not provided
if not settings.encryption_key:
    from cryptography.fernet import Fernet
    settings.encryption_key = Fernet.generate_key().decode()
    print(f"Generated encryption key: {settings.encryption_key}")
    print("Please add this to your .env file as ENCRYPTION_KEY")