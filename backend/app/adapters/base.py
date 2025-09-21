from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import httpx
import logging

logger = logging.getLogger(__name__)


class LLMRequest(BaseModel):
    """通用LLM请求"""
    model: str
    messages: List[Dict[str, Any]]
    max_tokens: int = 1000
    temperature: float = 0.7
    stream: bool = False


class LLMResponse(BaseModel):
    """通用LLM响应"""
    id: str
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class AbstractLLMAdapter(ABC):
    """LLM适配器抽象基类"""

    def __init__(self, api_key: str, api_url: Optional[str] = None):
        self.api_key = api_key
        self.api_url = api_url or self.get_default_api_url()
        self.client = httpx.AsyncClient(timeout=60.0)

    @abstractmethod
    def get_default_api_url(self) -> str:
        """获取默认API URL"""
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """验证API凭证是否有效"""
        pass

    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        pass

    @abstractmethod
    def transform_request_to_openai(self, request: LLMRequest) -> Dict[str, Any]:
        """转换请求为OpenAI格式"""
        pass

    @abstractmethod
    def transform_request_to_anthropic(self, request: LLMRequest) -> Dict[str, Any]:
        """转换请求为Anthropic格式"""
        pass

    @abstractmethod
    def transform_response_from_openai(self, response: Dict[str, Any]) -> LLMResponse:
        """从OpenAI格式转换响应"""
        pass

    @abstractmethod
    def transform_response_from_anthropic(self, response: Dict[str, Any]) -> LLMResponse:
        """从Anthropic格式转换响应"""
        pass

    async def send_request(self, data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """发送HTTP请求"""
        headers = self.get_headers()
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            response = await self.client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise

    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        pass

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

    def _extract_system_message(self, messages: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
        """提取系统消息"""
        system_message = ""
        filtered_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content", "")
            else:
                filtered_messages.append(msg)

        return system_message, filtered_messages

    def _ensure_message_format(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """确保消息格式正确"""
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "role": msg.get("role", "user"),
                "content": str(msg.get("content", ""))
            }
            formatted_messages.append(formatted_msg)
        return formatted_messages