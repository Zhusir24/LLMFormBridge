"""
阿里通义千问适配器测试用例
"""
import pytest
from app.adapters.qwen_adapter import QwenAdapter
from app.adapters.base import LLMRequest, LLMResponse


class TestQwenAdapter:
    """阿里通义千问适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建Qwen适配器实例"""
        return QwenAdapter(api_key="test_api_key")

    def test_initialization(self, adapter):
        """测试初始化"""
        assert adapter.api_key == "test_api_key"
        assert adapter.api_url == "https://dashscope.aliyuncs.com/api/v1"

    def test_default_api_url(self, adapter):
        """测试默认API URL"""
        assert adapter.get_default_api_url() == "https://dashscope.aliyuncs.com/api/v1"

    def test_get_headers(self, adapter):
        """测试请求头"""
        headers = adapter.get_headers()
        assert headers["Authorization"] == "Bearer test_api_key"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_available_models(self, adapter):
        """测试获取可用模型列表"""
        models = await adapter.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "qwen-turbo" in models
        assert "qwen-plus" in models
        assert "qwen-max" in models

    def test_transform_request_to_openai(self, adapter):
        """测试转换请求为OpenAI格式"""
        request = LLMRequest(
            model="qwen-turbo",
            messages=[
                {"role": "user", "content": "你好"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        openai_request = adapter.transform_request_to_openai(request)

        assert openai_request["model"] == "qwen-turbo"  # 保持原始模型名
        assert openai_request["messages"][0]["role"] == "user"
        assert openai_request["messages"][0]["content"] == "你好"
        assert openai_request["max_tokens"] == 100
        assert openai_request["temperature"] == 0.7

    def test_transform_request_to_anthropic(self, adapter):
        """测试转换请求为Anthropic格式"""
        request = LLMRequest(
            model="qwen-max",
            messages=[
                {"role": "system", "content": "你是一个助手"},
                {"role": "user", "content": "你好"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        anthropic_request = adapter.transform_request_to_anthropic(request)

        assert anthropic_request["model"] == "qwen-max"  # 保持原始模型名
        assert anthropic_request["system"] == "你是一个助手"
        assert len(anthropic_request["messages"]) == 1
        assert anthropic_request["messages"][0]["role"] == "user"

    def test_transform_request_to_qwen(self, adapter):
        """测试转换请求为通义千问格式"""
        request = LLMRequest(
            model="qwen-turbo",
            messages=[
                {"role": "system", "content": "你是一个助手"},
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好!"},
                {"role": "user", "content": "今天天气怎么样?"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        qwen_request = adapter.transform_request_to_qwen(request)

        # 检查基本结构
        assert "model" in qwen_request
        assert qwen_request["model"] == "qwen-turbo"
        assert "input" in qwen_request
        assert "parameters" in qwen_request

        # 检查消息（system消息应该在第一位）
        messages = qwen_request["input"]["messages"]
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "你是一个助手"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"

        # 检查参数
        params = qwen_request["parameters"]
        assert params["temperature"] == 0.7
        assert params["max_tokens"] == 100
        assert params["result_format"] == "message"

    def test_transform_response_from_qwen(self, adapter):
        """测试从通义千问格式转换响应"""
        qwen_response = {
            "request_id": "test-id",
            "output": {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "你好！我是通义千问，由阿里云开发的AI助手。"
                        },
                        "finish_reason": "stop"
                    }
                ]
            },
            "usage": {
                "input_tokens": 5,
                "output_tokens": 15,
                "total_tokens": 20
            }
        }

        llm_response = adapter.transform_response_from_qwen(qwen_response, "qwen-turbo")

        assert isinstance(llm_response, LLMResponse)
        assert llm_response.model == "qwen-turbo"
        assert len(llm_response.choices) == 1
        assert llm_response.choices[0]["message"]["role"] == "assistant"
        assert llm_response.choices[0]["message"]["content"] == "你好！我是通义千问，由阿里云开发的AI助手。"
        assert llm_response.choices[0]["finish_reason"] == "stop"
        assert llm_response.usage["prompt_tokens"] == 5
        assert llm_response.usage["completion_tokens"] == 15
        assert llm_response.usage["total_tokens"] == 20

    def test_model_mapping_to_openai(self, adapter):
        """测试模型映射到OpenAI"""
        assert adapter._map_model_to_openai("qwen-turbo") == "gpt-3.5-turbo"
        assert adapter._map_model_to_openai("qwen-plus") == "gpt-4"
        assert adapter._map_model_to_openai("qwen-max") == "gpt-4-turbo"
        assert adapter._map_model_to_openai("qwen-max-longcontext") == "gpt-4-turbo"

    def test_model_mapping_to_anthropic(self, adapter):
        """测试模型映射到Anthropic"""
        assert adapter._map_model_to_anthropic("qwen-turbo") == "claude-3-haiku-20240307"
        assert adapter._map_model_to_anthropic("qwen-plus") == "claude-3-5-sonnet-20241022"
        assert adapter._map_model_to_anthropic("qwen-max") == "claude-3-5-sonnet-20241022"

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
