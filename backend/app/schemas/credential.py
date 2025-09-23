from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime


class CredentialBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: Literal["openai", "anthropic", "claude_code"]
    api_url: Optional[str] = None


class CredentialCreate(CredentialBase):
    api_key: str = Field(..., min_length=1)

    @validator('api_url')
    def validate_api_url(cls, v, values):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('API URL must start with http:// or https://')
        return v


class CredentialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    api_key: Optional[str] = Field(None, min_length=1)
    api_url: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('api_url')
    def validate_api_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('API URL must start with http:// or https://')
        return v


class CredentialResponse(CredentialBase):
    id: str
    user_id: str
    is_active: bool
    is_validated: bool
    validation_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    api_key_masked: str  # 只显示前几位和后几位

    class Config:
        from_attributes = True


class CredentialValidate(BaseModel):
    """验证凭证响应"""
    is_valid: bool
    error_message: Optional[str] = None
    available_models: Optional[list[str]] = None