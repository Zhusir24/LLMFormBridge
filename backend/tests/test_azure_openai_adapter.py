"""
Azure OpenAI适配器测试用例
"""
import pytest
from app.adapters.azure_openai_adapter import AzureOpenAIAdapter
from app.adapters.base import LLMRequest, LLMResponse


class TestAzureOpenAIAdapter:
    """Azure OpenAI适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建Azure OpenAI适配器实例"""
        return AzureOpenAIAdapter(
            api_key="test_api_key:test_deployment",
            api_url="https://test-resource.openai.azure.com"
        )

    def test_initialization_with_deployment(self, adapter):
        """测试带deployment的初始化"""
        assert adapter.api_key == "test_api_key"
        assert adapter.deployment_name == "test_deployment"
        assert adapter.api_url == "https://test-resource.openai.azure.com"

    def test_initialization_without_deployment(self):
        """测试不带deployment的初始化"""
        adapter = AzureOpenAIAdapter(
            api_key="test_api_key",
            api_url="https://test-resource.openai.azure.com"
        )
        assert adapter.api_key == "test_api_key"
        assert adapter.deployment_name is None

    def test_initialization_requires_api_url(self):
        """测试必须提供API URL"""
        with pytest.raises(ValueError, match="requires api_url"):
            AzureOpenAIAdapter(api_key="test_api_key")

    def test_default_api_url_raises_error(self, adapter):
        """测试默认API URL会抛出错误"""
        with pytest.raises(ValueError, match="requires custom api_url"):
            adapter.get_default_api_url()

    def test_get_headers(self, adapter):
        """测试请求头（Azure使用api-key而非Authorization）"""
        headers = adapter.get_headers()
        assert headers["api-key"] == "test_api_key"
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers

    @pytest.mark.asyncio
    async def test_get_available_models(self, adapter):
        """测试获取可用模型列表"""
        models = await adapter.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "gpt-35-turbo" in models
        assert "gpt-4" in models
        assert "gpt-4o" in models

    def test_get_deployment_name_from_init(self, adapter):
        """测试从初始化参数获取deployment名称"""
        deployment = adapter._get_deployment_name("any-model")
        assert deployment == "test_deployment"

    def test_get_deployment_name_from_model(self):
        """测试从模型名称推断deployment名称"""
        adapter = AzureOpenAIAdapter(
            api_key="test_api_key",
            api_url="https://test-resource.openai.azure.com"
        )
        deployment = adapter._get_deployment_name("gpt-4")
        assert deployment == "gpt-4"

    def test_transform_request_to_openai(self, adapter):
        """测试转换请求为OpenAI格式"""
        request = LLMRequest(
            model="gpt-35-turbo",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        openai_request = adapter.transform_request_to_openai(request)

        assert openai_request["model"] == "gpt-35-turbo"
        assert openai_request["messages"][0]["role"] == "user"
        assert openai_request["messages"][0]["content"] == "Hello"
        assert openai_request["max_tokens"] == 100
        assert openai_request["temperature"] == 0.7

    def test_transform_request_to_anthropic(self, adapter):
        """测试转换请求为Anthropic格式"""
        request = LLMRequest(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        anthropic_request = adapter.transform_request_to_anthropic(request)

        assert anthropic_request["model"] == "gpt-4"  # 保持原始模型名
        assert anthropic_request["system"] == "You are a helpful assistant"
        assert len(anthropic_request["messages"]) == 1
        assert anthropic_request["messages"][0]["role"] == "user"

    def test_transform_response_from_openai(self, adapter):
        """测试从OpenAI格式转换响应"""
        openai_response = {
            "id": "test-id",
            "model": "gpt-35-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you today?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

        llm_response = adapter.transform_response_from_openai(openai_response)

        assert isinstance(llm_response, LLMResponse)
        assert llm_response.id == "test-id"
        assert llm_response.model == "gpt-35-turbo"
        assert len(llm_response.choices) == 1
        assert llm_response.choices[0]["message"]["content"] == "Hello! How can I help you today?"
        assert llm_response.usage["prompt_tokens"] == 10
        assert llm_response.usage["completion_tokens"] == 20
        assert llm_response.usage["total_tokens"] == 30

    def test_transform_response_from_anthropic(self, adapter):
        """测试从Anthropic格式转换响应"""
        anthropic_response = {
            "id": "test-id",
            "model": "claude-3-5-sonnet-20241022",
            "content": [
                {"type": "text", "text": "Test response"}
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20
            }
        }

        llm_response = adapter.transform_response_from_anthropic(anthropic_response)

        assert llm_response.model == "claude-3-5-sonnet-20241022"
        assert llm_response.choices[0]["message"]["content"] == "Test response"
        assert llm_response.usage["prompt_tokens"] == 10
        assert llm_response.usage["completion_tokens"] == 20

    def test_model_mapping_to_anthropic(self, adapter):
        """测试模型映射到Anthropic"""
        assert adapter._map_model_to_anthropic("gpt-35-turbo") == "claude-3-haiku-20240307"
        assert adapter._map_model_to_anthropic("gpt-4") == "claude-3-5-sonnet-20241022"
        assert adapter._map_model_to_anthropic("gpt-4-turbo") == "claude-3-5-sonnet-20241022"
        assert adapter._map_model_to_anthropic("gpt-4o") == "claude-3-5-sonnet-20241022"
