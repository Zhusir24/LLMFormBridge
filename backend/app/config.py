from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Application Settings
    app_name: str = "LLMFormBridge"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 3000

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
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Rate limiting
    rate_limit_per_minute: int = 100

    # Logging
    log_level: str = "INFO"

    # API Configuration
    api_base_path: str = "/api"
    openai_api_base_url: str = "https://api.openai.com/v1"
    anthropic_api_base_url: str = "https://api.anthropic.com"

    # Frontend Configuration
    frontend_url: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert allowed_origins string to list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    class Config:
        env_file = "../.env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()

# Generate encryption key if not provided
if not settings.encryption_key:
    from cryptography.fernet import Fernet
    settings.encryption_key = Fernet.generate_key().decode()
    print(f"Generated encryption key: {settings.encryption_key}")
    print("Please add this to your .env file as ENCRYPTION_KEY")