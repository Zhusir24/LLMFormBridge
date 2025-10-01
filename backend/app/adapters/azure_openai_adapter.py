from typing import Dict, Any, List, Optional
from .base import AbstractLLMAdapter, LLMRequest, LLMResponse
import uuid
import logging

logger = logging.getLogger(__name__)


class AzureOpenAIAdapter(AbstractLLMAdapter):
    """Azure OpenAI适配器"""

    def __init__(self, api_key: str, api_url: Optional[str] = None):
        """
        初始化Azure OpenAI适配器
        api_key格式: "API_KEY" 或 "API_KEY:DEPLOYMENT_NAME"
        api_url: Azure OpenAI资源的endpoint（必需）
        """
        # Azure可能需要deployment name，格式: "API_KEY:DEPLOYMENT_NAME"
        if ":" in api_key:
            self.api_key, self.deployment_name = api_key.split(":", 1)
        else:
            self.api_key = api_key
            self.deployment_name = None  # 将从模型名称推断

        if not api_url:
            raise ValueError("Azure OpenAI requires api_url (Azure endpoint)")

        self.api_url = api_url.rstrip("/")
        import httpx
        self.client = httpx.AsyncClient(timeout=60.0)

    def get_default_api_url(self) -> str:
        """Azure OpenAI没有默认URL，必须指定"""
        raise ValueError("Azure OpenAI requires custom api_url")

    def get_headers(self) -> Dict[str, str]:
        """Azure OpenAI的请求头"""
        return {
            "api-key": self.api_key,  # Azure使用api-key而非Authorization
            "Content-Type": "application/json"
        }

    def _get_deployment_name(self, model: str) -> str:
        """获取部署名称（从初始化参数或模型名称推断）"""
        if self.deployment_name:
            return self.deployment_name
        # 使用模型名称作为deployment名称
        return model

    async def send_request(self, data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """发送HTTP请求 - Azure OpenAI专用版本"""
        headers = self.get_headers()

        # Azure OpenAI的URL格式: https://{resource-name}.openai.azure.com/openai/deployments/{deployment-id}/chat/completions?api-version=2024-02-15-preview
        # 从data中提取模型名称来确定deployment
        model = data.get("model", "gpt-35-turbo")
        deployment = self._get_deployment_name(model)

        # 构建Azure特定的URL
        api_version = "2024-02-15-preview"
        url = f"{self.api_url}/openai/deployments/{deployment}/{endpoint.lstrip('/')}?api-version={api_version}"

        # 移除data中的model字段（Azure不需要）
        azure_data = {k: v for k, v in data.items() if k != "model"}

        try:
            import httpx
            response = await self.client.post(url, json=azure_data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise

    async def validate_credentials(self) -> bool:
        """验证Azure OpenAI凭证"""
        try:
            # 发送一个简单的测试请求
            test_request = {
                "model": "gpt-35-turbo",  # Azure常用的默认部署名
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 50
            }

            logger.info("Validating Azure OpenAI credentials")
            endpoint = "chat/completions"

            response = await self.send_request(test_request, endpoint)
            logger.info(f"Validation successful: {response}")
            return True
        except Exception as e:
            logger.error(f"Azure OpenAI credential validation failed: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """获取Azure OpenAI可用模型（需要根据用户的Azure部署配置）"""
        # Azure的模型名称取决于用户的部署配置
        # 返回常见的Azure OpenAI模型名称
        return [
            "gpt-35-turbo",
            "gpt-35-turbo-16k",
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-4o"
        ]

    def transform_request_to_openai(self, request: LLMRequest) -> Dict[str, Any]:
        """转换Azure OpenAI格式请求为OpenAI格式（基本相同）"""
        messages = self._ensure_message_format(request.messages)

        return {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }

    def transform_request_to_anthropic(self, request: LLMRequest) -> Dict[str, Any]:
        """转换Azure OpenAI格式请求为Anthropic格式"""
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
        """从OpenAI格式转换为Azure OpenAI格式响应（基本相同）"""
        return LLMResponse(
            id=response.get("id", str(uuid.uuid4())),
            model=response.get("model", "unknown"),
            choices=response.get("choices", []),
            usage=response.get("usage", {})
        )

    def transform_response_from_anthropic(self, response: Dict[str, Any]) -> LLMResponse:
        """从Anthropic格式转换为Azure OpenAI格式响应"""
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

    def _map_model_to_anthropic(self, azure_model: str) -> str:
        """映射Azure OpenAI模型名称到Anthropic"""
        model_mapping = {
            "gpt-35-turbo": "claude-3-haiku-20240307",
            "gpt-35-turbo-16k": "claude-3-haiku-20240307",
            "gpt-4": "claude-3-5-sonnet-20241022",
            "gpt-4-32k": "claude-3-5-sonnet-20241022",
            "gpt-4-turbo": "claude-3-5-sonnet-20241022",
            "gpt-4o": "claude-3-5-sonnet-20241022"
        }
        return model_mapping.get(azure_model, "claude-3-5-sonnet-20241022")

    async def forward_to_openai(self, request: LLMRequest) -> LLMResponse:
        """转发到Azure OpenAI"""
        azure_request = self.transform_request_to_openai(request)
        endpoint = "chat/completions"
        response = await self.send_request(azure_request, endpoint)
        return self.transform_response_from_openai(response)

    async def forward_to_anthropic_format(self, request: LLMRequest) -> Dict[str, Any]:
        """转发到Anthropic格式（不实际调用，只做转换）"""
        return self.transform_request_to_anthropic(request)
