from typing import Dict, Any, List, Optional
from .base import AbstractLLMAdapter, LLMRequest, LLMResponse
import uuid
import logging

logger = logging.getLogger(__name__)


class QwenAdapter(AbstractLLMAdapter):
    """阿里通义千问适配器"""

    def __init__(self, api_key: str, api_url: Optional[str] = None):
        self.api_key = api_key
        self.api_url = api_url or self.get_default_api_url()
        import httpx
        self.client = httpx.AsyncClient(timeout=60.0)

    def get_default_api_url(self) -> str:
        """通义千问的默认API URL"""
        return "https://dashscope.aliyuncs.com/api/v1"

    def get_headers(self) -> Dict[str, str]:
        """通义千问的请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def validate_credentials(self) -> bool:
        """验证通义千问凭证"""
        try:
            # 发送一个简单的测试请求
            test_request = {
                "model": "qwen-turbo",
                "input": {
                    "messages": [
                        {"role": "user", "content": "你好"}
                    ]
                },
                "parameters": {
                    "max_tokens": 50
                }
            }

            logger.info("Validating Alibaba Qwen credentials")
            endpoint = "services/aigc/text-generation/generation"

            response = await self.send_request(test_request, endpoint)
            logger.info(f"Validation successful: {response}")
            return True
        except Exception as e:
            logger.error(f"Alibaba Qwen credential validation failed: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """获取通义千问可用模型"""
        return [
            "qwen-turbo",
            "qwen-plus",
            "qwen-max",
            "qwen-max-longcontext",
            "qwen-vl-plus",
            "qwen-vl-max"
        ]

    def transform_request_to_openai(self, request: LLMRequest) -> Dict[str, Any]:
        """转换通义千问格式请求为OpenAI格式"""
        messages = self._ensure_message_format(request.messages)

        return {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }

    def transform_request_to_anthropic(self, request: LLMRequest) -> Dict[str, Any]:
        """转换通义千问格式请求为Anthropic格式"""
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

    def transform_request_to_qwen(self, request: LLMRequest) -> Dict[str, Any]:
        """转换标准请求为通义千问格式"""
        messages = self._ensure_message_format(request.messages)

        # 通义千问的消息格式
        qwen_messages = []
        system_content = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                # 通义千问支持system角色
                system_content = content
            else:
                qwen_messages.append({
                    "role": role,
                    "content": content
                })

        # 如果有system消息，添加到消息列表开头
        if system_content:
            qwen_messages.insert(0, {
                "role": "system",
                "content": system_content
            })

        qwen_request = {
            "model": request.model,
            "input": {
                "messages": qwen_messages
            },
            "parameters": {
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "result_format": "message"  # 使用message格式返回
            }
        }

        return qwen_request

    def transform_response_from_openai(self, response: Dict[str, Any]) -> LLMResponse:
        """从OpenAI格式转换为通义千问格式响应"""
        return LLMResponse(
            id=response.get("id", str(uuid.uuid4())),
            model=response.get("model", "unknown"),
            choices=response.get("choices", []),
            usage=response.get("usage", {})
        )

    def transform_response_from_anthropic(self, response: Dict[str, Any]) -> LLMResponse:
        """从Anthropic格式转换为通义千问格式响应"""
        choices = []
        content = response.get("content", [])

        if content and isinstance(content, list) and len(content) > 0:
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

    def transform_response_from_qwen(self, response: Dict[str, Any], model: str) -> LLMResponse:
        """从通义千问格式转换响应（转换为OpenAI格式以保持一致性）"""
        choices = []

        # 通义千问响应格式: {"output": {"choices": [{"message": {"role": "assistant", "content": "..."}}]}, "usage": {...}}
        output = response.get("output", {})
        qwen_choices = output.get("choices", [])

        if qwen_choices and len(qwen_choices) > 0:
            choice = qwen_choices[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            finish_reason = choice.get("finish_reason", "stop")

            choices.append({
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": finish_reason
            })

        # 通义千问的使用情况统计
        usage = response.get("usage", {})
        openai_usage = {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }

        return LLMResponse(
            id=response.get("request_id", str(uuid.uuid4())),
            model=model,
            choices=choices,
            usage=openai_usage
        )

    def _map_model_to_openai(self, qwen_model: str) -> str:
        """映射通义千问模型名称到OpenAI"""
        model_mapping = {
            "qwen-turbo": "gpt-3.5-turbo",
            "qwen-plus": "gpt-4",
            "qwen-max": "gpt-4-turbo",
            "qwen-max-longcontext": "gpt-4-turbo",
            "qwen-vl-plus": "gpt-4-vision-preview",
            "qwen-vl-max": "gpt-4-vision-preview"
        }
        return model_mapping.get(qwen_model, "gpt-4")

    def _map_model_to_anthropic(self, qwen_model: str) -> str:
        """映射通义千问模型名称到Anthropic"""
        model_mapping = {
            "qwen-turbo": "claude-3-haiku-20240307",
            "qwen-plus": "claude-3-5-sonnet-20241022",
            "qwen-max": "claude-3-5-sonnet-20241022",
            "qwen-max-longcontext": "claude-3-5-sonnet-20241022",
            "qwen-vl-plus": "claude-3-5-sonnet-20241022",
            "qwen-vl-max": "claude-3-5-sonnet-20241022"
        }
        return model_mapping.get(qwen_model, "claude-3-5-sonnet-20241022")

    async def forward_to_qwen(self, request: LLMRequest) -> LLMResponse:
        """转发到通义千问"""
        qwen_request = self.transform_request_to_qwen(request)
        endpoint = "services/aigc/text-generation/generation"
        response = await self.send_request(qwen_request, endpoint)
        return self.transform_response_from_qwen(response, request.model)

    async def forward_to_openai_format(self, request: LLMRequest) -> Dict[str, Any]:
        """转发到OpenAI格式（不实际调用，只做转换）"""
        return self.transform_request_to_openai(request)

    async def forward_to_anthropic_format(self, request: LLMRequest) -> Dict[str, Any]:
        """转发到Anthropic格式（不实际调用，只做转换）"""
        return self.transform_request_to_anthropic(request)
