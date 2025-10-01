"""
百度文心一言适配器测试用例
"""
import pytest
from app.adapters.ernie_adapter import ErnieAdapter
from app.adapters.base import LLMRequest, LLMResponse


class TestErnieAdapter:
    """百度文心一言适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建Ernie适配器实例"""
        return ErnieAdapter(api_key="test_api_key:test_secret_key")

    def test_initialization(self, adapter):
        """测试初始化"""
        assert adapter.api_key == "test_api_key"
        assert adapter.secret_key == "test_secret_key"
        assert adapter.api_url == "https://aip.baidubce.com/rpc/2.0/ai_custom/v1"

    def test_initialization_single_key(self):
        """测试单个key的初始化"""
        adapter = ErnieAdapter(api_key="single_key")
        assert adapter.api_key == "single_key"
        assert adapter.secret_key == ""

    def test_default_api_url(self, adapter):
        """测试默认API URL"""
        assert adapter.get_default_api_url() == "https://aip.baidubce.com/rpc/2.0/ai_custom/v1"

    def test_get_headers(self, adapter):
        """测试请求头"""
        headers = adapter.get_headers()
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_available_models(self, adapter):
        """测试获取可用模型列表"""
        models = await adapter.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "ERNIE-Bot" in models
        assert "ERNIE-Bot-turbo" in models
        assert "ERNIE-Bot-4" in models

    def test_transform_request_to_openai(self, adapter):
        """测试转换请求为OpenAI格式"""
        request = LLMRequest(
            model="ERNIE-Bot",
            messages=[
                {"role": "user", "content": "你好"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        openai_request = adapter.transform_request_to_openai(request)

        assert openai_request["model"] == "ERNIE-Bot"  # 保持原始模型名
        assert openai_request["messages"][0]["role"] == "user"
        assert openai_request["messages"][0]["content"] == "你好"
        assert openai_request["max_tokens"] == 100
        assert openai_request["temperature"] == 0.7

    def test_transform_request_to_anthropic(self, adapter):
        """测试转换请求为Anthropic格式"""
        request = LLMRequest(
            model="ERNIE-Bot-4",
            messages=[
                {"role": "system", "content": "你是一个助手"},
                {"role": "user", "content": "你好"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        anthropic_request = adapter.transform_request_to_anthropic(request)

        assert anthropic_request["model"] == "ERNIE-Bot-4"  # 保持原始模型名
        assert anthropic_request["system"] == "你是一个助手"
        assert len(anthropic_request["messages"]) == 1
        assert anthropic_request["messages"][0]["role"] == "user"

    def test_transform_request_to_ernie(self, adapter):
        """测试转换请求为文心一言格式"""
        request = LLMRequest(
            model="ERNIE-Bot",
            messages=[
                {"role": "system", "content": "你是一个助手"},
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好!"},
                {"role": "user", "content": "今天天气怎么样?"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        ernie_request = adapter.transform_request_to_ernie(request)

        # 检查消息（system消息应该合并到第一个user消息）
        assert "messages" in ernie_request
        assert len(ernie_request["messages"]) == 3  # 3个非system消息

        # 第一个user消息应该包含system内容
        assert ernie_request["messages"][0]["role"] == "user"
        assert "你是一个助手" in ernie_request["messages"][0]["content"]
        assert "你好" in ernie_request["messages"][0]["content"]

        # 检查其他配置
        assert ernie_request["temperature"] == 0.7
        assert ernie_request["max_output_tokens"] == 100

    def test_transform_response_from_ernie(self, adapter):
        """测试从文心一言格式转换响应"""
        ernie_response = {
            "id": "test-id",
            "result": "你好！我是百度开发的人工智能语言模型文心一言。",
            "is_truncated": False,
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 15,
                "total_tokens": 20
            }
        }

        llm_response = adapter.transform_response_from_ernie(ernie_response, "ERNIE-Bot")

        assert isinstance(llm_response, LLMResponse)
        assert llm_response.model == "ERNIE-Bot"
        assert len(llm_response.choices) == 1
        assert llm_response.choices[0]["message"]["role"] == "assistant"
        assert llm_response.choices[0]["message"]["content"] == "你好！我是百度开发的人工智能语言模型文心一言。"
        assert llm_response.choices[0]["finish_reason"] == "stop"
        assert llm_response.usage["prompt_tokens"] == 5
        assert llm_response.usage["completion_tokens"] == 15
        assert llm_response.usage["total_tokens"] == 20

    def test_transform_response_truncated(self, adapter):
        """测试转换被截断的响应"""
        ernie_response = {
            "id": "test-id",
            "result": "Test response",
            "is_truncated": True,
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 15,
                "total_tokens": 20
            }
        }

        llm_response = adapter.transform_response_from_ernie(ernie_response, "ERNIE-Bot")
        assert llm_response.choices[0]["finish_reason"] == "length"

    def test_model_mapping_to_openai(self, adapter):
        """测试模型映射到OpenAI"""
        assert adapter._map_model_to_openai("ERNIE-Bot") == "gpt-3.5-turbo"
        assert adapter._map_model_to_openai("ERNIE-Bot-turbo") == "gpt-3.5-turbo"
        assert adapter._map_model_to_openai("ERNIE-Bot-4") == "gpt-4"
        assert adapter._map_model_to_openai("ERNIE-Speed") == "gpt-3.5-turbo"

    def test_model_mapping_to_anthropic(self, adapter):
        """测试模型映射到Anthropic"""
        assert adapter._map_model_to_anthropic("ERNIE-Bot") == "claude-3-haiku-20240307"
        assert adapter._map_model_to_anthropic("ERNIE-Bot-4") == "claude-3-5-sonnet-20241022"

    def test_transform_response_from_openai(self, adapter):
        """测试从OpenAI格式转换响应"""
        openai_response = {
            "id": "test-id",
            "model": "gpt-3.5-turbo",
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
        assert llm_response.model == "gpt-3.5-turbo"
        assert llm_response.usage["prompt_tokens"] == 10

    def test_transform_response_from_anthropic(self, adapter):
        """测试从Anthropic格式转换响应"""
        anthropic_response = {
            "id": "test-id",
            "model": "claude-3-haiku-20240307",
            "content": [
                {"type": "text", "text": "Test response"}
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20
            }
        }

        llm_response = adapter.transform_response_from_anthropic(anthropic_response)

        assert llm_response.model == "claude-3-haiku-20240307"
        assert llm_response.choices[0]["message"]["content"] == "Test response"
        assert llm_response.usage["prompt_tokens"] == 10
