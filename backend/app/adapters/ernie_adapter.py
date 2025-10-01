from typing import Dict, Any, List, Optional
from .base import AbstractLLMAdapter, LLMRequest, LLMResponse
import uuid
import logging

logger = logging.getLogger(__name__)


class ErnieAdapter(AbstractLLMAdapter):
    """百度文心一言适配器"""

    def __init__(self, api_key: str, api_url: Optional[str] = None):
        # 百度使用API Key和Secret Key的组合，格式: "API_KEY:SECRET_KEY"
        if ":" in api_key:
            self.api_key, self.secret_key = api_key.split(":", 1)
        else:
            self.api_key = api_key
            self.secret_key = ""

        self.api_url = api_url or self.get_default_api_url()
        self.access_token = None  # 将通过API Key获取
        import httpx
        self.client = httpx.AsyncClient(timeout=60.0)

    def get_default_api_url(self) -> str:
        """文心一言的默认API URL"""
        return "https://aip.baidubce.com/rpc/2.0/ai_custom/v1"

    def get_headers(self) -> Dict[str, str]:
        """文心一言的请求头"""
        return {
            "Content-Type": "application/json"
        }

    async def get_access_token(self) -> str:
        """获取百度access_token"""
        if self.access_token:
            return self.access_token

        try:
            import httpx
            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params)
                response.raise_for_status()
                result = response.json()
                self.access_token = result.get("access_token", "")
                return self.access_token
        except Exception as e:
            logger.error(f"Failed to get Baidu access token: {e}")
            raise

    async def send_request(self, data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """发送HTTP请求 - 文心一言专用版本"""
        headers = self.get_headers()
        access_token = await self.get_access_token()

        # 文心一言通过查询参数传递access_token
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}?access_token={access_token}"

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
        """验证文心一言凭证"""
        try:
            # 获取access token即可验证凭证
            await self.get_access_token()

            # 发送一个简单的测试请求
            test_request = {
                "messages": [
                    {"role": "user", "content": "你好"}
                ]
            }

            logger.info("Validating Baidu ERNIE credentials")
            endpoint = "wenxinworkshop/chat/completions"

            response = await self.send_request(test_request, endpoint)
            logger.info(f"Validation successful: {response}")
            return True
        except Exception as e:
            logger.error(f"Baidu ERNIE credential validation failed: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """获取文心一言可用模型"""
        return [
            "ERNIE-Bot",
            "ERNIE-Bot-turbo",
            "ERNIE-Bot-4",
            "ERNIE-Speed",
            "ERNIE-Lite",
            "ERNIE-Tiny"
        ]

    def transform_request_to_openai(self, request: LLMRequest) -> Dict[str, Any]:
        """转换文心一言格式请求为OpenAI格式"""
        messages = self._ensure_message_format(request.messages)

        return {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }

    def transform_request_to_anthropic(self, request: LLMRequest) -> Dict[str, Any]:
        """转换文心一言格式请求为Anthropic格式"""
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

    def transform_request_to_ernie(self, request: LLMRequest) -> Dict[str, Any]:
        """转换标准请求为文心一言格式"""
        messages = self._ensure_message_format(request.messages)

        # 文心一言的消息格式与OpenAI类似，但有细微差异
        ernie_messages = []
        system_content = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                # 文心一言不直接支持system角色，将其合并到第一条user消息
                system_content = content
            else:
                ernie_messages.append({
                    "role": role,
                    "content": content
                })

        # 如果有system消息，合并到第一条user消息
        if system_content and ernie_messages:
            for i, msg in enumerate(ernie_messages):
                if msg["role"] == "user":
                    ernie_messages[i]["content"] = f"{system_content}\n\n{msg['content']}"
                    break

        ernie_request = {
            "messages": ernie_messages,
            "temperature": request.temperature,
            "max_output_tokens": request.max_tokens  # 文心一言使用max_output_tokens
        }

        return ernie_request

    def transform_response_from_openai(self, response: Dict[str, Any]) -> LLMResponse:
        """从OpenAI格式转换为文心一言格式响应"""
        return LLMResponse(
            id=response.get("id", str(uuid.uuid4())),
            model=response.get("model", "unknown"),
            choices=response.get("choices", []),
            usage=response.get("usage", {})
        )

    def transform_response_from_anthropic(self, response: Dict[str, Any]) -> LLMResponse:
        """从Anthropic格式转换为文心一言格式响应"""
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

    def transform_response_from_ernie(self, response: Dict[str, Any], model: str) -> LLMResponse:
        """从文心一言格式转换响应（转换为OpenAI格式以保持一致性）"""
        choices = []

        # 文心一言响应格式: {"result": "...", "is_truncated": false, ...}
        result_text = response.get("result", "")
        is_truncated = response.get("is_truncated", False)

        choices.append({
            "index": 0,
            "message": {
                "role": "assistant",
                "content": result_text
            },
            "finish_reason": "length" if is_truncated else "stop"
        })

        # 文心一言的使用情况统计
        usage = response.get("usage", {})
        openai_usage = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }

        return LLMResponse(
            id=response.get("id", str(uuid.uuid4())),
            model=model,
            choices=choices,
            usage=openai_usage
        )

    def _map_model_to_openai(self, ernie_model: str) -> str:
        """映射文心一言模型名称到OpenAI"""
        model_mapping = {
            "ERNIE-Bot": "gpt-3.5-turbo",
            "ERNIE-Bot-turbo": "gpt-3.5-turbo",
            "ERNIE-Bot-4": "gpt-4",
            "ERNIE-Speed": "gpt-3.5-turbo",
            "ERNIE-Lite": "gpt-3.5-turbo",
            "ERNIE-Tiny": "gpt-3.5-turbo"
        }
        return model_mapping.get(ernie_model, "gpt-3.5-turbo")

    def _map_model_to_anthropic(self, ernie_model: str) -> str:
        """映射文心一言模型名称到Anthropic"""
        model_mapping = {
            "ERNIE-Bot": "claude-3-haiku-20240307",
            "ERNIE-Bot-turbo": "claude-3-haiku-20240307",
            "ERNIE-Bot-4": "claude-3-5-sonnet-20241022",
            "ERNIE-Speed": "claude-3-haiku-20240307",
            "ERNIE-Lite": "claude-3-haiku-20240307",
            "ERNIE-Tiny": "claude-3-haiku-20240307"
        }
        return model_mapping.get(ernie_model, "claude-3-haiku-20240307")

    async def forward_to_ernie(self, request: LLMRequest) -> LLMResponse:
        """转发到文心一言"""
        ernie_request = self.transform_request_to_ernie(request)
        # 文心一言使用统一的endpoint
        endpoint = "wenxinworkshop/chat/completions"
        response = await self.send_request(ernie_request, endpoint)
        return self.transform_response_from_ernie(response, request.model)

    async def forward_to_openai_format(self, request: LLMRequest) -> Dict[str, Any]:
        """转发到OpenAI格式（不实际调用，只做转换）"""
        return self.transform_request_to_openai(request)

    async def forward_to_anthropic_format(self, request: LLMRequest) -> Dict[str, Any]:
        """转发到Anthropic格式（不实际调用，只做转换）"""
        return self.transform_request_to_anthropic(request)
