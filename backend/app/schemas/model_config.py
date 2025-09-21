from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime


class ModelConfigBase(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=100)
    target_format: Literal["openai", "anthropic"]
    is_enabled: bool = True
    rate_limit: int = Field(default=100, ge=1, le=10000)


class ModelConfigCreate(ModelConfigBase):
    credential_id: str

    @validator('target_format')
    def validate_target_format(cls, v, values):
        # 可以添加更多验证逻辑，比如检查模型名称和格式的兼容性
        return v


class ModelConfigUpdate(BaseModel):
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_format: Optional[Literal["openai", "anthropic"]] = None
    is_enabled: Optional[bool] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)


class ModelConfigResponse(ModelConfigBase):
    id: str
    credential_id: str
    proxy_api_key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelConfigWithCredential(ModelConfigResponse):
    """包含凭证信息的模型配置"""
    credential_name: str
    credential_provider: str