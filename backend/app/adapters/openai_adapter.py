from typing import Dict, Any, List
from .base import AbstractLLMAdapter, LLMRequest, LLMResponse
import time
import uuid
import logging

logger = logging.getLogger(__name__)


class OpenAIAdapter(AbstractLLMAdapter):
    """OpenAI适配器"""

    def get_default_api_url(self) -> str:
        return "https://api.openai.com/v1"

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def validate_credentials(self) -> bool:
        """验证OpenAI凭证"""
        try:
            await self.get_available_models()
            return True
        except Exception as e:
            logger.error(f"OpenAI credential validation failed: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """获取OpenAI可用模型"""
        try:
            response = await self.send_request({}, "models")
            models = [model["id"] for model in response.get("data", [])]
            return models
        except Exception as e:
            logger.error(f"Failed to get OpenAI models: {e}")
            return []

    def transform_request_to_openai(self, request: LLMRequest) -> Dict[str, Any]:
        """转换请求为OpenAI格式（已经是OpenAI格式）"""
        messages = self._ensure_message_format(request.messages)

        return {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }

    def transform_request_to_anthropic(self, request: LLMRequest) -> Dict[str, Any]:
        """转换OpenAI格式请求为Anthropic格式"""
        system_message, messages = self._extract_system_message(request.messages)
        formatted_messages = self._ensure_message_format(messages)

        anthropic_request = {
            "model": request.model,
            "messages": formatted_messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }

        if system_message:
            anthropic_request["system"] = system_message

        return anthropic_request

    def transform_response_from_openai(self, response: Dict[str, Any]) -> LLMResponse:
        """从OpenAI格式转换响应（已经是标准格式）"""
        return LLMResponse(
            id=response.get("id", str(uuid.uuid4())),
            model=response.get("model", "unknown"),
            choices=response.get("choices", []),
            usage=response.get("usage", {})
        )

    def transform_response_from_anthropic(self, response: Dict[str, Any]) -> LLMResponse:
        """从Anthropic格式转换为OpenAI格式响应"""
        # 转换Anthropic响应为OpenAI格式
        choices = []
        if "content" in response:
            content = response["content"]
            if isinstance(content, list) and content:
                text = content[0].get("text", "")
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

    def _map_model_to_anthropic(self, openai_model: str) -> str:
        """映射OpenAI模型名称到Anthropic"""
        model_mapping = {
            "gpt-4": "claude-3-5-sonnet-20241022",
            "gpt-4-turbo": "claude-3-5-sonnet-20241022",
            "gpt-3.5-turbo": "claude-3-haiku-20240307",
        }
        return model_mapping.get(openai_model, "claude-3-5-sonnet-20241022")

    async def forward_to_openai(self, request: LLMRequest) -> LLMResponse:
        """转发到OpenAI"""
        openai_request = self.transform_request_to_openai(request)
        response = await self.send_request(openai_request, "chat/completions")
        return self.transform_response_from_openai(response)

    async def forward_to_anthropic_format(self, request: LLMRequest) -> Dict[str, Any]:
        """转发到Anthropic格式"""
        # 这里需要实际调用Anthropic API，但我们在OpenAI适配器中模拟
        # 实际使用时应该使用AnthropicAdapter
        raise NotImplementedError("Use AnthropicAdapter for Anthropic API calls")