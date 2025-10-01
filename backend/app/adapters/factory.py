from typing import Dict, Type, Optional
from .base import AbstractLLMAdapter
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .claude_code_adapter import ClaudeCodeAdapter
from .gemini_adapter import GeminiAdapter
from .ernie_adapter import ErnieAdapter
from .qwen_adapter import QwenAdapter
from .azure_openai_adapter import AzureOpenAIAdapter


class LLMAdapterFactory:
    """LLM适配器工厂"""

    _adapters: Dict[str, Type[AbstractLLMAdapter]] = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "claude_code": ClaudeCodeAdapter,
        "gemini": GeminiAdapter,
        "ernie": ErnieAdapter,
        "qwen": QwenAdapter,
        "azure_openai": AzureOpenAIAdapter,
    }

    @classmethod
    def create_adapter(
        cls,
        provider: str,
        api_key: str,
        api_url: Optional[str] = None
    ) -> AbstractLLMAdapter:
        """创建适配器实例"""
        # 自动检测Claude Code凭证
        if provider == "anthropic" and api_key.startswith("cr_"):
            provider = "claude_code"

        if provider not in cls._adapters:
            raise ValueError(f"Unsupported provider: {provider}. Available: {list(cls._adapters.keys())}")

        adapter_class = cls._adapters[provider]
        return adapter_class(api_key=api_key, api_url=api_url)

    @classmethod
    def register_adapter(cls, provider: str, adapter_class: Type[AbstractLLMAdapter]):
        """注册新的适配器类型"""
        cls._adapters[provider] = adapter_class

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """获取支持的提供商列表"""
        return list(cls._adapters.keys())

    @classmethod
    def is_provider_supported(cls, provider: str) -> bool:
        """检查是否支持某个提供商"""
        return provider in cls._adapters