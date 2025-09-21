from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import uuid


class Message(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class LLMRequest(BaseModel):
    """通用LLM请求格式"""
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4000)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    stream: Optional[bool] = False


class LLMResponse(BaseModel):
    """通用LLM响应格式"""
    id: str
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class OpenAIRequest(BaseModel):
    """OpenAI格式请求"""
    model: str
    messages: List[Dict[str, str]]
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None


class OpenAIResponse(BaseModel):
    """OpenAI格式响应"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class AnthropicRequest(BaseModel):
    """Anthropic格式请求"""
    model: str
    messages: List[Dict[str, str]]
    max_tokens: int = 1000
    temperature: Optional[float] = 0.7
    system: Optional[str] = None


class AnthropicResponse(BaseModel):
    """Anthropic格式响应"""
    id: str
    type: str = "message"
    role: str = "assistant"
    content: List[Dict[str, Any]]
    model: str
    usage: Dict[str, int]


class ProxyRequest(BaseModel):
    """代理请求信息"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_format: str
    target_format: str
    original_request: Dict[str, Any]