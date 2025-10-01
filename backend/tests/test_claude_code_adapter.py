"""
Claude Code适配器测试用例
"""
import pytest
from app.adapters.claude_code_adapter import ClaudeCodeAdapter
from app.adapters.base import LLMRequest, LLMResponse


class TestClaudeCodeAdapter:
    """Claude Code适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建Claude Code适配器实例"""
        return ClaudeCodeAdapter(api_key="cr_test_api_key")

    def test_initialization(self, adapter):
        """测试初始化"""
        assert adapter.api_key == "cr_test_api_key"
        assert adapter.api_url == "https://api.claude.ai/v1"

    def test_initialization_requires_cr_prefix(self):
        """测试必须使用cr_前缀的API key"""
        with pytest.raises(ValueError, match="requires API key starting with 'cr_'"):
            ClaudeCodeAdapter(api_key="test_api_key")

    def test_custom_api_url(self):
        """测试自定义API URL"""
        adapter = ClaudeCodeAdapter(
            api_key="cr_test_api_key",
            api_url="https://custom.claude.ai/v1"
        )
        assert adapter.api_url == "https://custom.claude.ai/v1"

    def test_default_api_url(self, adapter):
        """测试默认API URL"""
        assert adapter.get_default_api_url() == "https://api.claude.ai/v1"

    def test_get_headers(self, adapter):
        """测试请求头"""
        headers = adapter.get_headers()
        assert headers["Authorization"] == "Bearer cr_test_api_key"
        assert headers["Content-Type"] == "application/json"
        assert headers["anthropic-version"] == "2023-06-01"
        assert headers["User-Agent"] == "claude-cli/1.0.102 (external, cli)"
        assert headers["x-app"] == "cli"
        assert headers["x-stainless-retry-count"] == "0"
        assert headers["x-stainless-timeout"] == "60"

    @pytest.mark.asyncio
    async def test_get_available_models(self, adapter):
        """测试获取可用模型列表"""
        models = await adapter.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "claude-3-5-sonnet-20241022" in models
        assert "claude-sonnet-4-20250514" in models
        assert "claude-opus-4-20250514" in models
        assert "claude-3-7-sonnet-20250219" in models

    def test_transform_request_to_anthropic(self, adapter):
        """测试转换请求为Claude Code格式"""
        request = LLMRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {"role": "system", "content": "You are a programming assistant"},
                {"role": "user", "content": "Help me write code"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        claude_request = adapter.transform_request_to_anthropic(request)

        assert claude_request["model"] == "claude-3-5-sonnet-20241022"
        assert len(claude_request["messages"]) == 1
        assert claude_request["messages"][0]["role"] == "user"
        assert claude_request["max_tokens"] == 100
        assert claude_request["temperature"] == 0.7

        # 检查system字段（应该是数组格式）
        assert isinstance(claude_request["system"], list)
        assert len(claude_request["system"]) == 2
        # 第一个是Claude Code系统提示词
        assert claude_request["system"][0]["type"] == "text"
        assert "cache_control" in claude_request["system"][0]
        # 第二个是自定义系统消息
        assert claude_request["system"][1]["type"] == "text"
        assert claude_request["system"][1]["text"] == "You are a programming assistant"

    def test_transform_request_to_anthropic_without_custom_system(self, adapter):
        """测试转换请求为Claude Code格式（无自定义系统消息）"""
        request = LLMRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=50,
            temperature=0.5
        )

        claude_request = adapter.transform_request_to_anthropic(request)

        assert claude_request["model"] == "claude-3-5-sonnet-20241022"
        # 应该只有Claude Code默认系统提示词
        assert isinstance(claude_request["system"], list)
        assert len(claude_request["system"]) == 1
        assert claude_request["system"][0]["type"] == "text"
        assert "cache_control" in claude_request["system"][0]

    def test_transform_request_to_openai(self, adapter):
        """测试转换请求为OpenAI格式"""
        request = LLMRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        openai_request = adapter.transform_request_to_openai(request)

        assert openai_request["model"] == "claude-3-5-sonnet-20241022"  # 保持原始模型名
        assert len(openai_request["messages"]) == 1
        # 系统消息应该合并到第一个用户消息中
        assert openai_request["messages"][0]["role"] == "user"
        assert "You are a helpful assistant" in openai_request["messages"][0]["content"]
        assert "Hello" in openai_request["messages"][0]["content"]

    def test_transform_request_to_openai_without_system(self, adapter):
        """测试转换请求为OpenAI格式（无系统消息）"""
        request = LLMRequest(
            model="claude-sonnet-4-20250514",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=50,
            temperature=0.5
        )

        openai_request = adapter.transform_request_to_openai(request)

        assert openai_request["model"] == "claude-sonnet-4-20250514"  # 保持原始模型名
        assert len(openai_request["messages"]) == 1
        assert openai_request["messages"][0]["role"] == "user"
        assert openai_request["messages"][0]["content"] == "Hello"

    def test_transform_response_from_anthropic(self, adapter):
        """测试从Claude Code格式转换响应"""
        claude_response = {
            "id": "test-id",
            "model": "claude-3-5-sonnet-20241022",
            "content": [
                {"type": "text", "text": "Here is the code you requested..."}
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20
            }
        }

        llm_response = adapter.transform_response_from_anthropic(claude_response)

        assert isinstance(llm_response, LLMResponse)
        assert llm_response.id == "test-id"
        assert llm_response.model == "claude-3-5-sonnet-20241022"
        assert len(llm_response.choices) == 1
        assert llm_response.choices[0]["message"]["role"] == "assistant"
        assert llm_response.choices[0]["message"]["content"] == "Here is the code you requested..."
        assert llm_response.choices[0]["finish_reason"] == "stop"
        assert llm_response.usage["prompt_tokens"] == 10
        assert llm_response.usage["completion_tokens"] == 20
        assert llm_response.usage["total_tokens"] == 30

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
                        "content": "Here is the response"
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
        assert llm_response.choices[0]["message"]["content"] == "Here is the response"
        assert llm_response.usage["prompt_tokens"] == 10

    def test_model_mapping_to_openai(self, adapter):
        """测试模型映射到OpenAI"""
        assert adapter._map_model_to_openai("claude-3-5-sonnet-20241022") == "gpt-4-turbo"
        assert adapter._map_model_to_openai("claude-3-opus-20240229") == "gpt-4"
        assert adapter._map_model_to_openai("claude-3-haiku-20240307") == "gpt-3.5-turbo"
        assert adapter._map_model_to_openai("claude-sonnet-4-20250514") == "gpt-4-turbo"
        assert adapter._map_model_to_openai("claude-opus-4-20250514") == "gpt-4o"
