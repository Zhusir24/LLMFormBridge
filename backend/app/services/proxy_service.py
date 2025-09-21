from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.models.model_config import ModelConfig
from app.models.credential import Credential
from app.models.request_log import RequestLog
from app.adapters.factory import LLMAdapterFactory
from app.adapters.base import LLMRequest, LLMResponse
from app.utils.security import decrypt_api_key
from app.exceptions import LLMProviderError, RateLimitError
from app.schemas.llm_request import OpenAIRequest, AnthropicRequest
import time
import uuid
import logging

logger = logging.getLogger(__name__)


class ProxyService:
    def __init__(self, db: Session):
        self.db = db

    def get_config_by_proxy_key(self, proxy_api_key: str) -> Optional[ModelConfig]:
        """根据代理API密钥获取模型配置"""
        return self.db.query(ModelConfig).filter(
            ModelConfig.proxy_api_key == proxy_api_key
        ).first()

    def validate_rate_limit(self, config: ModelConfig) -> bool:
        """验证速率限制"""
        # 简化实现：检查最近1分钟的请求数量
        from datetime import datetime, timedelta

        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_requests = self.db.query(RequestLog).filter(
            RequestLog.model_config_id == config.id,
            RequestLog.created_at >= one_minute_ago
        ).count()

        return recent_requests < config.rate_limit

    async def proxy_openai_request(
        self,
        proxy_api_key: str,
        request_data: OpenAIRequest
    ) -> Dict[str, Any]:
        """代理OpenAI格式请求"""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # 获取模型配置
        config = self.get_config_by_proxy_key(proxy_api_key)
        if not config or not config.is_enabled:
            raise LLMProviderError("Invalid or disabled API key")

        # 验证速率限制
        if not self.validate_rate_limit(config):
            raise RateLimitError("Rate limit exceeded")

        # 获取凭证
        credential = config.credential
        if not credential or not credential.is_active or not credential.is_validated:
            raise LLMProviderError("Invalid or inactive credential")

        try:
            # 解密API密钥
            api_key = decrypt_api_key(credential.api_key_encrypted)

            # 创建适配器
            adapter = LLMAdapterFactory.create_adapter(
                provider=credential.provider,
                api_key=api_key,
                api_url=credential.api_url
            )

            # 转换请求
            llm_request = LLMRequest(
                model=request_data.model,
                messages=request_data.messages,
                max_tokens=request_data.max_tokens,
                temperature=request_data.temperature,
                stream=request_data.stream
            )

            # 根据目标格式转发请求
            if config.target_format == "openai":
                if credential.provider == "openai":
                    response = await adapter.forward_to_openai(llm_request)
                else:
                    # Anthropic -> OpenAI format
                    response = await adapter.forward_to_anthropic(llm_request)
            else:  # target_format == "anthropic"
                if credential.provider == "anthropic":
                    response = await adapter.forward_to_anthropic(llm_request)
                else:
                    # OpenAI -> Anthropic format
                    response = await adapter.forward_to_openai(llm_request)

            # 转换响应为OpenAI格式
            if config.target_format == "openai":
                # 对于OpenAI格式，直接返回响应（已经是OpenAI格式）
                final_response = response.dict()
            else:
                # 转换为Anthropic格式
                final_response = self._convert_to_anthropic_response(response.dict())

            # 记录日志
            self._log_request(
                config=config,
                request_id=request_id,
                method="POST",
                path="/api/v1/chat/completions",
                source_format="openai",
                target_format=config.target_format,
                status_code=200,
                response_time_ms=int((time.time() - start_time) * 1000),
                tokens_used=response.usage.get("total_tokens", 0)
            )

            await adapter.close()
            return final_response

        except Exception as e:
            logger.error(f"Proxy request failed: {e}")

            # 记录错误日志
            self._log_request(
                config=config,
                request_id=request_id,
                method="POST",
                path="/api/v1/chat/completions",
                source_format="openai",
                target_format=config.target_format,
                status_code=500,
                response_time_ms=int((time.time() - start_time) * 1000),
                error_message=str(e)
            )

            raise LLMProviderError(f"Request failed: {str(e)}")

    async def proxy_anthropic_request(
        self,
        proxy_api_key: str,
        request_data: AnthropicRequest
    ) -> Dict[str, Any]:
        """代理Anthropic格式请求"""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # 获取模型配置
        config = self.get_config_by_proxy_key(proxy_api_key)
        if not config or not config.is_enabled:
            raise LLMProviderError("Invalid or disabled API key")

        # 验证速率限制
        if not self.validate_rate_limit(config):
            raise RateLimitError("Rate limit exceeded")

        # 获取凭证
        credential = config.credential
        if not credential or not credential.is_active or not credential.is_validated:
            raise LLMProviderError("Invalid or inactive credential")

        try:
            # 解密API密钥
            api_key = decrypt_api_key(credential.api_key_encrypted)

            # 创建适配器
            adapter = LLMAdapterFactory.create_adapter(
                provider=credential.provider,
                api_key=api_key,
                api_url=credential.api_url
            )

            # 构建系统消息
            messages = request_data.messages.copy()
            if request_data.system:
                messages.insert(0, {"role": "system", "content": request_data.system})

            # 转换请求
            llm_request = LLMRequest(
                model=request_data.model,
                messages=messages,
                max_tokens=request_data.max_tokens,
                temperature=request_data.temperature
            )

            # 根据目标格式转发请求
            if config.target_format == "anthropic":
                if credential.provider == "anthropic":
                    response = await adapter.forward_to_anthropic(llm_request)
                else:
                    # OpenAI -> Anthropic format
                    response = await adapter.forward_to_openai(llm_request)
            else:  # target_format == "openai"
                if credential.provider == "openai":
                    response = await adapter.forward_to_openai(llm_request)
                else:
                    # Anthropic -> OpenAI format
                    response = await adapter.forward_to_anthropic(llm_request)

            # 转换响应为Anthropic格式
            if config.target_format == "anthropic":
                if credential.provider == "anthropic":
                    final_response = self._convert_to_anthropic_response(response.dict())
                else:
                    # 从OpenAI格式转换
                    final_response = self._convert_to_anthropic_response(response.dict())
            else:
                # 保持OpenAI格式
                final_response = response.dict()

            # 记录日志
            self._log_request(
                config=config,
                request_id=request_id,
                method="POST",
                path="/api/v1/messages",
                source_format="anthropic",
                target_format=config.target_format,
                status_code=200,
                response_time_ms=int((time.time() - start_time) * 1000),
                tokens_used=response.usage.get("total_tokens", 0)
            )

            await adapter.close()
            return final_response

        except Exception as e:
            logger.error(f"Proxy request failed: {e}")

            # 记录错误日志
            self._log_request(
                config=config,
                request_id=request_id,
                method="POST",
                path="/api/v1/messages",
                source_format="anthropic",
                target_format=config.target_format,
                status_code=500,
                response_time_ms=int((time.time() - start_time) * 1000),
                error_message=str(e)
            )

            raise LLMProviderError(f"Request failed: {str(e)}")

    def _convert_to_anthropic_response(self, openai_response: Dict[str, Any]) -> Dict[str, Any]:
        """将OpenAI响应转换为Anthropic格式"""
        choices = openai_response.get("choices", [])
        content = []

        if choices:
            message = choices[0].get("message", {})
            text = message.get("content", "")
            content = [{"type": "text", "text": text}]

        usage = openai_response.get("usage", {})

        return {
            "id": openai_response.get("id", str(uuid.uuid4())),
            "type": "message",
            "role": "assistant",
            "content": content,
            "model": openai_response.get("model", "unknown"),
            "usage": {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0)
            }
        }

    def _log_request(
        self,
        config: ModelConfig,
        request_id: str,
        method: str,
        path: str,
        source_format: str,
        target_format: str,
        status_code: int,
        response_time_ms: int,
        tokens_used: int = 0,
        error_message: str = None
    ):
        """记录请求日志"""
        log = RequestLog(
            model_config_id=config.id,
            request_id=request_id,
            method=method,
            path=path,
            source_format=source_format,
            target_format=target_format,
            status_code=status_code,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            error_message=error_message
        )

        self.db.add(log)
        self.db.commit()

    def get_available_models(self, proxy_api_key: str) -> list[str]:
        """获取可用模型列表"""
        config = self.get_config_by_proxy_key(proxy_api_key)
        if not config or not config.is_enabled:
            return []

        # 返回配置的模型
        return [config.model_name]