"""
Google Gemini适配器测试用例
"""
import pytest
from app.adapters.gemini_adapter import GeminiAdapter
from app.adapters.base import LLMRequest, LLMResponse


class TestGeminiAdapter:
    """Google Gemini适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建Gemini适配器实例"""
        return GeminiAdapter(api_key="test_api_key")

    def test_initialization(self, adapter):
        """测试初始化"""
        assert adapter.api_key == "test_api_key"
        assert adapter.api_url == "https://generativelanguage.googleapis.com/v1beta"

    def test_default_api_url(self, adapter):
        """测试默认API URL"""
        assert adapter.get_default_api_url() == "https://generativelanguage.googleapis.com/v1beta"

    def test_get_headers(self, adapter):
        """测试请求头"""
        headers = adapter.get_headers()
        assert headers["Content-Type"] == "application/json"
        # Gemini使用查询参数传递API key，不在header中

    @pytest.mark.asyncio
    async def test_get_available_models(self, adapter):
        """测试获取可用模型列表"""
        models = await adapter.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "gemini-pro" in models
        assert "gemini-1.5-pro" in models
        assert "gemini-1.5-flash" in models

    def test_transform_request_to_openai(self, adapter):
        """测试转换请求为OpenAI格式"""
        request = LLMRequest(
            model="gemini-pro",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        openai_request = adapter.transform_request_to_openai(request)

        assert openai_request["model"] == "gemini-pro"  # 保持原始模型名
        assert openai_request["messages"][0]["role"] == "user"
        assert openai_request["messages"][0]["content"] == "Hello"
        assert openai_request["max_tokens"] == 100
        assert openai_request["temperature"] == 0.7

    def test_transform_request_to_anthropic(self, adapter):
        """测试转换请求为Anthropic格式"""
        request = LLMRequest(
            model="gemini-pro",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        anthropic_request = adapter.transform_request_to_anthropic(request)

        assert anthropic_request["model"] == "gemini-pro"  # 保持原始模型名
        assert anthropic_request["system"] == "You are a helpful assistant"
        assert len(anthropic_request["messages"]) == 1
        assert anthropic_request["messages"][0]["role"] == "user"
        assert anthropic_request["max_tokens"] == 100

    def test_transform_request_to_gemini(self, adapter):
        """测试转换请求为Gemini格式"""
        request = LLMRequest(
            model="gemini-pro",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        gemini_request = adapter.transform_request_to_gemini(request)

        # 检查systemInstruction
        assert "systemInstruction" in gemini_request
        assert gemini_request["systemInstruction"]["parts"][0]["text"] == "You are a helpful assistant"

        # 检查contents
        assert "contents" in gemini_request
        assert len(gemini_request["contents"]) == 3  # 3个非system消息

        # 检查角色映射（assistant -> model）
        assert gemini_request["contents"][0]["role"] == "user"
        assert gemini_request["contents"][1]["role"] == "model"
        assert gemini_request["contents"][2]["role"] == "user"

        # 检查generationConfig
        assert gemini_request["generationConfig"]["temperature"] == 0.7
        assert gemini_request["generationConfig"]["maxOutputTokens"] == 100

    def test_transform_response_from_gemini(self, adapter):
        """测试从Gemini格式转换响应"""
        gemini_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Hello! How can I help you today?"}
                        ]
                    },
                    "finishReason": "STOP"
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 20,
                "totalTokenCount": 30
            }
        }

        llm_response = adapter.transform_response_from_gemini(gemini_response, "gemini-pro")

        assert isinstance(llm_response, LLMResponse)
        assert llm_response.model == "gemini-pro"
        assert len(llm_response.choices) == 1
        assert llm_response.choices[0]["message"]["role"] == "assistant"
        assert llm_response.choices[0]["message"]["content"] == "Hello! How can I help you today?"
        assert llm_response.choices[0]["finish_reason"] == "stop"
        assert llm_response.usage["prompt_tokens"] == 10
        assert llm_response.usage["completion_tokens"] == 20
        assert llm_response.usage["total_tokens"] == 30

    def test_model_mapping_to_openai(self, adapter):
        """测试模型映射到OpenAI"""
        assert adapter._map_model_to_openai("gemini-pro") == "gpt-4"
        assert adapter._map_model_to_openai("gemini-1.5-pro") == "gpt-4-turbo"
        assert adapter._map_model_to_openai("gemini-1.5-flash") == "gpt-3.5-turbo"
        assert adapter._map_model_to_openai("gemini-pro-vision") == "gpt-4-vision-preview"

    def test_model_mapping_to_anthropic(self, adapter):
        """测试模型映射到Anthropic"""
        assert adapter._map_model_to_anthropic("gemini-pro") == "claude-3-5-sonnet-20241022"
        assert adapter._map_model_to_anthropic("gemini-1.5-pro") == "claude-3-5-sonnet-20241022"
        assert adapter._map_model_to_anthropic("gemini-1.5-flash") == "claude-3-haiku-20240307"

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
                        "content": "Test response"
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

        assert llm_response.id == "test-id"
        assert llm_response.model == "gpt-4"
        assert len(llm_response.choices) == 1
        assert llm_response.usage["prompt_tokens"] == 10

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
