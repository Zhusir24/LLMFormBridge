"""
OpenAI适配器测试用例
"""
import pytest
from app.adapters.openai_adapter import OpenAIAdapter
from app.adapters.base import LLMRequest, LLMResponse


class TestOpenAIAdapter:
    """OpenAI适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建OpenAI适配器实例"""
        return OpenAIAdapter(api_key="test_api_key")

    def test_initialization(self, adapter):
        """测试初始化"""
        assert adapter.api_key == "test_api_key"
        assert adapter.api_url == "https://api.openai.com/v1"

    def test_default_api_url(self, adapter):
        """测试默认API URL"""
        assert adapter.get_default_api_url() == "https://api.openai.com/v1"

    def test_custom_api_url(self):
        """测试自定义API URL"""
        adapter = OpenAIAdapter(
            api_key="test_api_key",
            api_url="https://custom.openai.com/v1"
        )
        assert adapter.api_url == "https://custom.openai.com/v1"

    def test_get_headers(self, adapter):
        """测试请求头"""
        headers = adapter.get_headers()
        assert headers["Authorization"] == "Bearer test_api_key"
        assert headers["Content-Type"] == "application/json"

    def test_transform_request_to_openai(self, adapter):
        """测试转换请求为OpenAI格式（保持原样）"""
        request = LLMRequest(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        openai_request = adapter.transform_request_to_openai(request)

        assert openai_request["model"] == "gpt-4"
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
        assert anthropic_request["messages"][0]["content"] == "Hello"
        assert anthropic_request["max_tokens"] == 100
        assert anthropic_request["temperature"] == 0.7

    def test_transform_request_to_anthropic_without_system(self, adapter):
        """测试转换请求为Anthropic格式（无系统消息）"""
        request = LLMRequest(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=50,
            temperature=0.5
        )

        anthropic_request = adapter.transform_request_to_anthropic(request)

        assert anthropic_request["model"] == "gpt-3.5-turbo"  # 保持原始模型名
        assert "system" not in anthropic_request
        assert len(anthropic_request["messages"]) == 1

    def test_transform_response_from_openai(self, adapter):
        """测试从OpenAI格式转换响应"""
        openai_response = {
            "id": "test-id",
            "model": "gpt-4",
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
        assert llm_response.model == "gpt-4"
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
                {"type": "text", "text": "Hello! How can I assist you?"}
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20
            }
        }

        llm_response = adapter.transform_response_from_anthropic(anthropic_response)

        assert isinstance(llm_response, LLMResponse)
        assert llm_response.id == "test-id"
        assert llm_response.model == "claude-3-5-sonnet-20241022"
        assert len(llm_response.choices) == 1
        assert llm_response.choices[0]["message"]["role"] == "assistant"
        assert llm_response.choices[0]["message"]["content"] == "Hello! How can I assist you?"
        assert llm_response.choices[0]["finish_reason"] == "stop"
        assert llm_response.usage["prompt_tokens"] == 10
        assert llm_response.usage["completion_tokens"] == 20
        assert llm_response.usage["total_tokens"] == 30

    def test_model_mapping_to_anthropic(self, adapter):
        """测试模型映射到Anthropic"""
        assert adapter._map_model_to_anthropic("gpt-4") == "claude-3-5-sonnet-20241022"
        assert adapter._map_model_to_anthropic("gpt-4-turbo") == "claude-3-5-sonnet-20241022"
        assert adapter._map_model_to_anthropic("gpt-3.5-turbo") == "claude-3-haiku-20240307"
