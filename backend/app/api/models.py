from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
    ModelConfigWithCredential
)
from app.services.model_service import ModelService
from app.exceptions import CredentialValidationError

router = APIRouter(prefix="/api/models", tags=["Model Configurations"])


@router.get("/", response_model=List[ModelConfigWithCredential])
@router.get("", response_model=List[ModelConfigWithCredential])
async def get_model_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有模型配置"""
    model_service = ModelService(db)
    configs = model_service.get_model_configs_with_credential(current_user)
    return configs


@router.post("/", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_model_config(
    config_data: ModelConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新的模型配置"""
    try:
        model_service = ModelService(db)
        config = model_service.create_model_config(current_user, config_data)
        return config
    except CredentialValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{config_id}", response_model=ModelConfigResponse)
async def get_model_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个模型配置"""
    model_service = ModelService(db)
    config = model_service.get_model_config_by_id(current_user, config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model configuration not found"
        )

    return config


@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_model_config(
    config_id: str,
    update_data: ModelConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新模型配置"""
    try:
        model_service = ModelService(db)
        config = model_service.update_model_config(current_user, config_id, update_data)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model configuration not found"
            )

        return config
    except CredentialValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{config_id}")
@router.delete("/{config_id}/")
async def delete_model_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除模型配置"""
    model_service = ModelService(db)
    success = model_service.delete_model_config(current_user, config_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model configuration not found"
        )

    return {"message": "Model configuration deleted successfully"}


@router.post("/{config_id}/regenerate-key")
async def regenerate_proxy_api_key(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新生成代理API密钥"""
    model_service = ModelService(db)
    new_key = model_service.regenerate_proxy_api_key(current_user, config_id)

    if not new_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model configuration not found"
        )

    return {"proxy_api_key": new_key}


@router.get("/{config_id}/info")
async def get_model_config_info(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取模型配置详细信息"""
    model_service = ModelService(db)
    config = model_service.get_model_config_by_id(current_user, config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model configuration not found"
        )

    # 获取关联的凭证信息
    credential = config.credential

    return {
        "id": config.id,
        "model_name": config.model_name,
        "target_format": config.target_format,
        "is_enabled": config.is_enabled,
        "rate_limit": config.rate_limit,
        "proxy_api_key": config.proxy_api_key,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
        "credential": {
            "id": credential.id,
            "name": credential.name,
            "provider": credential.provider,
            "is_validated": credential.is_validated
        },
        "proxy_endpoint": f"/api/v1/chat/completions" if config.target_format == "openai" else f"/api/v1/messages"
    }