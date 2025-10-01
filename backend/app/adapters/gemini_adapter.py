from typing import Dict, Any, List, Optional
from .base import AbstractLLMAdapter, LLMRequest, LLMResponse
import uuid
import logging

logger = logging.getLogger(__name__)


class GeminiAdapter(AbstractLLMAdapter):
    """Google Gemini适配器"""

    def __init__(self, api_key: str, api_url: Optional[str] = None):
        self.api_key = api_key
        self.api_url = api_url or self.get_default_api_url()
        # Gemini使用API key作为查询参数，不需要特殊的HTTP客户端
        import httpx
        self.client = httpx.AsyncClient(timeout=60.0)

    def get_default_api_url(self) -> str:
        """Gemini的默认API URL"""
        return "https://generativelanguage.googleapis.com/v1beta"

    def get_headers(self) -> Dict[str, str]:
        """Gemini使用查询参数而非header传递API key"""
        return {
            "Content-Type": "application/json"
        }

    async def send_request(self, data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """发送HTTP请求 - Gemini专用版本（API key作为查询参数）"""
        headers = self.get_headers()
        # Gemini的API key通过查询参数传递
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}?key={self.api_key}"

        try:
            import httpx
            response = await self.client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise

    async def validate_credentials(self) -> bool:
        """验证Gemini凭证"""
        try:
            # 发送一个简单的测试请求
            test_request = {
                "contents": [
                    {
                        "parts": [
                            {"text": "Hi"}
                        ]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 50
                }
            }

            logger.info(f"Validating Gemini credentials")
            endpoint = "models/gemini-pro:generateContent"

            response = await self.send_request(test_request, endpoint)
            logger.info(f"Validation successful: {response}")
            return True
        except Exception as e:
            logger.error(f"Gemini credential validation failed: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """获取Gemini可用模型"""
        return [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b"
        ]

    def transform_request_to_openai(self, request: LLMRequest) -> Dict[str, Any]:
        """转换Gemini格式请求为OpenAI格式"""
        messages = self._ensure_message_format(request.messages)

        return {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }

    def transform_request_to_anthropic(self, request: LLMRequest) -> Dict[str, Any]:
        """转换Gemini格式请求为Anthropic格式"""
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

    def transform_request_to_gemini(self, request: LLMRequest) -> Dict[str, Any]:
        """转换标准请求为Gemini格式"""
        messages = self._ensure_message_format(request.messages)

        # Gemini使用不同的消息格式
        contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                # Gemini 1.5支持systemInstruction
                system_instruction = {"parts": [{"text": content}]}
            elif role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role == "assistant":
                contents.append({
                    "role": "model",  # Gemini使用"model"代替"assistant"
                    "parts": [{"text": content}]
                })

        gemini_request = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens
            }
        }

        if system_instruction:
            gemini_request["systemInstruction"] = system_instruction

        return gemini_request

    def transform_response_from_openai(self, response: Dict[str, Any]) -> LLMResponse:
        """从OpenAI格式转换为Gemini格式响应"""
        return LLMResponse(
            id=response.get("id", str(uuid.uuid4())),
            model=response.get("model", "unknown"),
            choices=response.get("choices", []),
            usage=response.get("usage", {})
        )

    def transform_response_from_anthropic(self, response: Dict[str, Any]) -> LLMResponse:
        """从Anthropic格式转换为Gemini格式响应"""
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

    def transform_response_from_gemini(self, response: Dict[str, Any], model: str) -> LLMResponse:
        """从Gemini格式转换响应（转换为OpenAI格式以保持一致性）"""
        choices = []

        # Gemini响应格式: {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
        candidates = response.get("candidates", [])
        if candidates and len(candidates) > 0:
            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            if parts and len(parts) > 0:
                text = parts[0].get("text", "")
            else:
                text = ""

            finish_reason = candidate.get("finishReason", "STOP").lower()
            if finish_reason == "stop":
                finish_reason = "stop"
            elif finish_reason == "max_tokens":
                finish_reason = "length"
            else:
                finish_reason = "stop"

            choices.append({
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text
                },
                "finish_reason": finish_reason
            })

        # Gemini的使用情况统计
        usage_metadata = response.get("usageMetadata", {})
        openai_usage = {
            "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
            "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
            "total_tokens": usage_metadata.get("totalTokenCount", 0)
        }

        return LLMResponse(
            id=str(uuid.uuid4()),
            model=model,
            choices=choices,
            usage=openai_usage
        )

    def _map_model_to_openai(self, gemini_model: str) -> str:
        """映射Gemini模型名称到OpenAI"""
        model_mapping = {
            "gemini-pro": "gpt-4",
            "gemini-pro-vision": "gpt-4-vision-preview",
            "gemini-1.5-pro": "gpt-4-turbo",
            "gemini-1.5-flash": "gpt-3.5-turbo",
            "gemini-1.5-flash-8b": "gpt-3.5-turbo"
        }
        return model_mapping.get(gemini_model, "gpt-4")

    def _map_model_to_anthropic(self, gemini_model: str) -> str:
        """映射Gemini模型名称到Anthropic"""
        model_mapping = {
            "gemini-pro": "claude-3-5-sonnet-20241022",
            "gemini-pro-vision": "claude-3-5-sonnet-20241022",
            "gemini-1.5-pro": "claude-3-5-sonnet-20241022",
            "gemini-1.5-flash": "claude-3-haiku-20240307",
            "gemini-1.5-flash-8b": "claude-3-haiku-20240307"
        }
        return model_mapping.get(gemini_model, "claude-3-5-sonnet-20241022")

    async def forward_to_gemini(self, request: LLMRequest) -> LLMResponse:
        """转发到Gemini"""
        gemini_request = self.transform_request_to_gemini(request)
        # 使用模型名称构建endpoint
        model_name = request.model
        endpoint = f"models/{model_name}:generateContent"
        response = await self.send_request(gemini_request, endpoint)
        return self.transform_response_from_gemini(response, request.model)

    async def forward_to_openai_format(self, request: LLMRequest) -> Dict[str, Any]:
        """转发到OpenAI格式（不实际调用，只做转换）"""
        return self.transform_request_to_openai(request)

    async def forward_to_anthropic_format(self, request: LLMRequest) -> Dict[str, Any]:
        """转发到Anthropic格式（不实际调用，只做转换）"""
        return self.transform_request_to_anthropic(request)
