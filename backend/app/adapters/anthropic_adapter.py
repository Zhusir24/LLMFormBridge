from typing import Dict, Any, List, Optional
from .base import AbstractLLMAdapter, LLMRequest, LLMResponse
import time
import uuid
import logging
import httpx

logger = logging.getLogger(__name__)


class AnthropicAdapter(AbstractLLMAdapter):
    """Anthropic适配器"""

    def __init__(self, api_key: str, api_url: Optional[str] = None):
        self.api_key = api_key
        self.api_url = api_url or self.get_default_api_url()
        # 为Claude Code专用凭证创建特殊的HTTP客户端配置
        if self.api_url != self.get_default_api_url() and self.api_key.startswith("cr_"):
            # 创建没有默认头部的干净客户端
            self.client = httpx.AsyncClient(
                timeout=60.0,
                headers={}  # 不使用任何默认头部
            )
        else:
            self.client = httpx.AsyncClient(timeout=60.0)

    def get_default_api_url(self) -> str:
        return "https://api.anthropic.com/v1"

    def get_headers(self) -> Dict[str, str]:
        # 为Claude Code专用凭证使用简化的headers（基于成功的curl命令）
        if self.api_url != self.get_default_api_url() and self.api_key.startswith("cr_"):
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
                "User-Agent": "claude-cli/1.0.102 (external, cli)",
                "Accept": "application/json",
                "x-stainless-retry-count": "0",
                "x-stainless-timeout": "60",
                "x-app": "cli"
            }
        else:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }

        return headers

    async def send_request(self, data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """发送HTTP请求 - Claude Code专用版本"""
        headers = self.get_headers()
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # 为Claude Code专用凭证使用特殊的请求方式，避免httpx添加默认headers
        if self.api_url != self.get_default_api_url() and self.api_key.startswith("cr_"):
            try:
                # 创建一个全新的临时客户端，确保不会添加任何意外的headers
                async with httpx.AsyncClient(timeout=60.0) as temp_client:
                    response = await temp_client.post(url, json=data, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Request error: {e}")
                raise
        else:
            # 使用父类的标准方法
            return await super().send_request(data, endpoint)

    async def validate_credentials(self) -> bool:
        """验证Anthropic凭证"""
        try:
            # 发送一个简单的测试请求（使用支持的模型）
            test_request = {
                "model": "claude-3-5-sonnet-20241022",  # 使用支持的模型
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 50  # 减少token数量，加快验证速度
            }

            # 为Claude Code专用凭证添加必需的system字段格式
            if self.api_url != self.get_default_api_url() and self.api_key.startswith("cr_"):
                test_request["system"] = [
                    {
                        "type": "text",
                        "text": "You are Claude Code, Anthropic's official CLI for Claude.",
                        "cache_control": {
                            "type": "ephemeral"
                        }
                    }
                ]
                logger.info(f"Using Claude Code format for URL: {self.api_url}")

            # 修正路径：claude-relay-service使用标准API路径
            if self.api_url != self.get_default_api_url():
                # claude-relay-service 和其他自定义服务使用 v1/messages
                endpoint = "v1/messages"
            else:
                # 官方Anthropic API使用 messages
                endpoint = "messages"
            
            logger.info(f"Validating credentials with endpoint: {endpoint}")
            logger.info(f"Request headers: {self.get_headers()}")
            logger.info(f"Request data: {test_request}")
            
            response = await self.send_request(test_request, endpoint)
            logger.info(f"Validation successful: {response}")
            return True
        except Exception as e:
            logger.error(f"Anthropic credential validation failed: {e}")
            logger.error(f"API URL: {self.api_url}")
            logger.error(f"API Key prefix: {self.api_key[:10]}...")
            return False

    async def get_available_models(self) -> List[str]:
        """获取Anthropic可用模型"""
        # 为Claude Code专用凭证，返回claude-relay-service支持的模型
        if self.api_url != self.get_default_api_url() and self.api_key.startswith("cr_"):
            return [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022", 
                "claude-3-opus-20240229",
                "claude-sonnet-4-20250514"  # claude-relay-service特有的模型
            ]
        else:
            # 官方Anthropic API支持的模型
            return [
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]

    def transform_request_to_openai(self, request: LLMRequest) -> Dict[str, Any]:
        """转换Anthropic格式请求为OpenAI格式"""
        messages = self._ensure_message_format(request.messages)

        # 如果有系统消息，需要合并到第一个用户消息中
        system_content = ""
        filtered_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content", "")
            else:
                filtered_messages.append(msg)

        # 如果有系统消息，添加到第一个用户消息前
        if system_content and filtered_messages:
            first_user_msg = None
            for i, msg in enumerate(filtered_messages):
                if msg.get("role") == "user":
                    first_user_msg = i
                    break

            if first_user_msg is not None:
                original_content = filtered_messages[first_user_msg]["content"]
                filtered_messages[first_user_msg]["content"] = f"{system_content}\n\n{original_content}"

        return {
            "model": self._map_model_to_openai(request.model),
            "messages": filtered_messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }

    def transform_request_to_anthropic(self, request: LLMRequest) -> Dict[str, Any]:
        """转换请求为Anthropic格式（已经是Anthropic格式）"""
        system_message, messages = self._extract_system_message(request.messages)
        formatted_messages = self._ensure_message_format(messages)

        anthropic_request = {
            "model": request.model,
            "messages": formatted_messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }

        # 为Claude Code专用凭证设置特殊的system格式
        if self.api_url != self.get_default_api_url() and self.api_key.startswith("cr_"):
            # claude-relay-service要求system字段为数组格式，且必须包含Claude Code系统提示词
            claude_code_system = {
                "type": "text",
                "text": "You are Claude Code, Anthropic's official CLI for Claude.",
                "cache_control": {
                    "type": "ephemeral"
                }
            }

            if system_message:
                # 如果有自定义system消息，添加到Claude Code系统提示词后
                anthropic_request["system"] = [
                    claude_code_system,
                    {
                        "type": "text",
                        "text": system_message
                    }
                ]
            else:
                # 只使用Claude Code系统提示词
                anthropic_request["system"] = [claude_code_system]
        else:
            # 标准Anthropic API使用字符串格式
            if system_message:
                anthropic_request["system"] = system_message

        return anthropic_request

    def transform_response_from_openai(self, response: Dict[str, Any]) -> LLMResponse:
        """从OpenAI格式转换为Anthropic格式响应"""
        # 这是为了统一接口，实际返回OpenAI格式
        return LLMResponse(
            id=response.get("id", str(uuid.uuid4())),
            model=response.get("model", "unknown"),
            choices=response.get("choices", []),
            usage=response.get("usage", {})
        )

    def transform_response_from_anthropic(self, response: Dict[str, Any]) -> LLMResponse:
        """从Anthropic格式转换响应（转换为OpenAI格式以保持一致性）"""
        choices = []
        content = response.get("content", [])

        if content and isinstance(content, list) and len(content) > 0:
            # 检查第一个内容项是否有text字段
            first_item = content[0]
            if isinstance(first_item, dict) and "text" in first_item:
                text = first_item.get("text", "")
            else:
                text = str(first_item)
        elif isinstance(content, str):
            text = content
        else:
            text = str(content)

        choices.append({
            "index": 0,
            "message": {
                "role": "assistant",
                "content": text
            },
            "finish_reason": "stop"
        })

        usage = response.get("usage", {})
        openai_usage = {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        }

        return LLMResponse(
            id=response.get("id", str(uuid.uuid4())),
            model=response.get("model", "unknown"),
            choices=choices,
            usage=openai_usage
        )

    def _map_model_to_openai(self, anthropic_model: str) -> str:
        """映射Anthropic模型名称到OpenAI"""
        model_mapping = {
            "claude-3-5-sonnet-20241022": "gpt-4-turbo",
            "claude-3-opus-20240229": "gpt-4",
            "claude-3-sonnet-20240229": "gpt-4",
            "claude-3-haiku-20240307": "gpt-3.5-turbo",
        }
        return model_mapping.get(anthropic_model, "gpt-4")

    async def forward_to_anthropic(self, request: LLMRequest) -> LLMResponse:
        """转发到Anthropic"""
        anthropic_request = self.transform_request_to_anthropic(request)
        # 修正路径：claude-relay-service使用标准API路径
        if self.api_url != self.get_default_api_url():
            # claude-relay-service 和其他自定义服务使用 v1/messages
            endpoint = "v1/messages"
        else:
            # 官方Anthropic API使用 messages
            endpoint = "messages"
        response = await self.send_request(anthropic_request, endpoint)
        return self.transform_response_from_anthropic(response)

    async def forward_to_openai_format(self, _request: LLMRequest) -> Dict[str, Any]:
        """转发到OpenAI格式"""
        # 这里需要实际调用OpenAI API，但我们在Anthropic适配器中模拟
        # 实际使用时应该使用OpenAIAdapter
        raise NotImplementedError("Use OpenAIAdapter for OpenAI API calls")