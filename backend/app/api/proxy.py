from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.schemas.llm_request import OpenAIRequest, AnthropicRequest
from app.services.proxy_service import ProxyService
from app.exceptions import LLMProviderError, RateLimitError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["LLM Proxy"])
security = HTTPBearer()


def get_api_key_from_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """从Authorization头获取API密钥"""
    return credentials.credentials


@router.post("/chat/completions")
async def openai_chat_completions(
    request_data: OpenAIRequest,
    api_key: str = Depends(get_api_key_from_auth),
    db: Session = Depends(get_db)
):
    """OpenAI兼容的聊天完成接口"""
    try:
        proxy_service = ProxyService(db)
        response = await proxy_service.proxy_openai_request(api_key, request_data)
        return response

    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except LLMProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in OpenAI proxy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/messages")
async def anthropic_messages(
    request_data: AnthropicRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Anthropic兼容的消息接口"""
    # Anthropic使用x-api-key头
    api_key = request.headers.get("x-api-key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-api-key header"
        )

    try:
        proxy_service = ProxyService(db)
        response = await proxy_service.proxy_anthropic_request(api_key, request_data)
        return response

    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except LLMProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in Anthropic proxy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/models")
async def list_models(
    api_key: str = Depends(get_api_key_from_auth),
    db: Session = Depends(get_db)
):
    """获取可用模型列表（OpenAI兼容）"""
    try:
        proxy_service = ProxyService(db)
        models = proxy_service.get_available_models(api_key)

        # 返回OpenAI格式的模型列表
        model_objects = []
        for model in models:
            model_objects.append({
                "id": model,
                "object": "model",
                "created": 1677610602,
                "owned_by": "llmbridge"
            })

        return {
            "object": "list",
            "data": model_objects
        }

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list models"
        )


@router.get("/health")
async def proxy_health_check():
    """代理服务健康检查"""
    return {"status": "healthy", "service": "llm-proxy"}


# 添加一个简单的测试端点
@router.post("/test")
async def test_proxy(
    request_data: Dict[str, Any],
    api_key: str = Depends(get_api_key_from_auth),
    db: Session = Depends(get_db)
):
    """测试代理功能"""
    proxy_service = ProxyService(db)
    config = proxy_service.get_config_by_proxy_key(api_key)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return {
        "message": "Proxy is working",
        "config": {
            "model_name": config.model_name,
            "target_format": config.target_format,
            "is_enabled": config.is_enabled,
            "rate_limit": config.rate_limit
        }
    }