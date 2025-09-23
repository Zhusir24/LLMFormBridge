from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.credential import (
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialValidate
)
from app.services.credential_service import CredentialService
from app.exceptions import CredentialValidationError

router = APIRouter(prefix="/api/credentials", tags=["Credentials"])


@router.get("/", response_model=List[CredentialResponse])
@router.get("", response_model=List[CredentialResponse])
async def get_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有凭证"""
    credential_service = CredentialService(db)
    credentials = credential_service.get_user_credentials(current_user)

    # 转换为响应格式，包含遮盖的API密钥
    response_credentials = []
    for cred in credentials:
        response_cred = CredentialResponse(
            id=cred.id,
            user_id=cred.user_id,
            name=cred.name,
            provider=cred.provider,
            api_url=cred.api_url,
            custom_models=cred.custom_models or [],
            model_validation_results=cred.model_validation_results or {},
            is_active=cred.is_active,
            is_validated=cred.is_validated,
            validation_error=cred.validation_error,
            created_at=cred.created_at,
            updated_at=cred.updated_at,
            api_key_masked=credential_service.mask_api_key(cred.api_key_encrypted)
        )
        response_credentials.append(response_cred)

    return response_credentials


@router.post("/", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    credential_data: CredentialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新凭证"""
    try:
        credential_service = CredentialService(db)
        credential = credential_service.create_credential(current_user, credential_data)

        return CredentialResponse(
            id=credential.id,
            user_id=credential.user_id,
            name=credential.name,
            provider=credential.provider,
            api_url=credential.api_url,
            custom_models=credential.custom_models or [],
            model_validation_results=credential.model_validation_results or {},
            is_active=credential.is_active,
            is_validated=credential.is_validated,
            validation_error=credential.validation_error,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
            api_key_masked=credential_service.mask_api_key(credential.api_key_encrypted)
        )
    except CredentialValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个凭证"""
    credential_service = CredentialService(db)
    credential = credential_service.get_credential_by_id(current_user, credential_id)

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )

    return CredentialResponse(
        id=credential.id,
        user_id=credential.user_id,
        name=credential.name,
        provider=credential.provider,
        api_url=credential.api_url,
        custom_models=credential.custom_models or [],
        model_validation_results=credential.model_validation_results or {},
        is_active=credential.is_active,
        is_validated=credential.is_validated,
        validation_error=credential.validation_error,
        created_at=credential.created_at,
        updated_at=credential.updated_at,
        api_key_masked=credential_service.mask_api_key(credential.api_key_encrypted)
    )


@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: str,
    update_data: CredentialUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新凭证"""
    try:
        credential_service = CredentialService(db)
        credential = credential_service.update_credential(current_user, credential_id, update_data)

        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )

        return CredentialResponse(
            id=credential.id,
            user_id=credential.user_id,
            name=credential.name,
            provider=credential.provider,
            api_url=credential.api_url,
            custom_models=credential.custom_models or [],
            model_validation_results=credential.model_validation_results or {},
            is_active=credential.is_active,
            is_validated=credential.is_validated,
            validation_error=credential.validation_error,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
            api_key_masked=credential_service.mask_api_key(credential.api_key_encrypted)
        )
    except CredentialValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{credential_id}")
@router.delete("/{credential_id}/")
async def delete_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除凭证"""
    credential_service = CredentialService(db)
    success = credential_service.delete_credential(current_user, credential_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )

    return {"message": "Credential deleted successfully"}


@router.post("/{credential_id}/validate", response_model=CredentialValidate)
async def validate_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """验证凭证"""
    try:
        credential_service = CredentialService(db)
        result = await credential_service.validate_credential(current_user, credential_id)
        return result
    except CredentialValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{credential_id}/models")
async def get_credential_available_models(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取凭证支持的可用模型"""
    try:
        credential_service = CredentialService(db)
        models = await credential_service.get_available_models(current_user, credential_id)
        return {"models": models}
    except CredentialValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )