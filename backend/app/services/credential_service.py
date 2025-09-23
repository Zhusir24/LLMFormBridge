from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict
from app.models.credential import Credential
from app.models.user import User
from app.schemas.credential import CredentialCreate, CredentialUpdate, CredentialValidate
from app.utils.security import encrypt_api_key, decrypt_api_key
from app.adapters.factory import LLMAdapterFactory
from app.exceptions import CredentialValidationError
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class CredentialService:
    def __init__(self, db: Session):
        self.db = db

    def create_credential(self, user: User, credential_data: CredentialCreate) -> Credential:
        """创建新凭证"""
        # 检查名称是否重复
        existing = self.db.query(Credential).filter(
            and_(
                Credential.user_id == user.id,
                Credential.name == credential_data.name
            )
        ).first()

        if existing:
            raise CredentialValidationError(f"Credential name '{credential_data.name}' already exists")

        # 加密API密钥
        encrypted_api_key = encrypt_api_key(credential_data.api_key)

        # 创建凭证
        credential = Credential(
            user_id=user.id,
            name=credential_data.name,
            provider=credential_data.provider,
            api_key_encrypted=encrypted_api_key,
            api_url=credential_data.api_url,
            custom_models=credential_data.custom_models
        )

        self.db.add(credential)
        self.db.commit()
        self.db.refresh(credential)

        return credential

    def get_user_credentials(self, user: User) -> List[Credential]:
        """获取用户的所有凭证"""
        return self.db.query(Credential).filter(Credential.user_id == user.id).all()

    def get_credential_by_id(self, user: User, credential_id: str) -> Optional[Credential]:
        """根据ID获取凭证"""
        return self.db.query(Credential).filter(
            and_(
                Credential.id == credential_id,
                Credential.user_id == user.id
            )
        ).first()

    def update_credential(self, user: User, credential_id: str, update_data: CredentialUpdate) -> Optional[Credential]:
        """更新凭证"""
        credential = self.get_credential_by_id(user, credential_id)
        if not credential:
            return None

        # 检查名称是否重复（如果更新了名称）
        if update_data.name and update_data.name != credential.name:
            existing = self.db.query(Credential).filter(
                and_(
                    Credential.user_id == user.id,
                    Credential.name == update_data.name,
                    Credential.id != credential_id
                )
            ).first()

            if existing:
                raise CredentialValidationError(f"Credential name '{update_data.name}' already exists")

        # 更新字段
        if update_data.name is not None:
            credential.name = update_data.name

        if update_data.api_key is not None:
            credential.api_key_encrypted = encrypt_api_key(update_data.api_key)
            # 重置验证状态
            credential.is_validated = False
            credential.validation_error = None

        if update_data.api_url is not None:
            credential.api_url = update_data.api_url

        if update_data.custom_models is not None:
            credential.custom_models = update_data.custom_models
            # 如果模型列表发生变化，重置验证状态
            credential.is_validated = False
            credential.validation_error = None

        if update_data.is_active is not None:
            credential.is_active = update_data.is_active

        self.db.commit()
        self.db.refresh(credential)

        return credential

    def delete_credential(self, user: User, credential_id: str) -> bool:
        """删除凭证"""
        credential = self.get_credential_by_id(user, credential_id)
        if not credential:
            return False

        self.db.delete(credential)
        self.db.commit()
        return True

    async def validate_credential(self, user: User, credential_id: str) -> CredentialValidate:
        """验证凭证 - 支持多模型并行验证"""
        credential = self.get_credential_by_id(user, credential_id)
        if not credential:
            raise CredentialValidationError("Credential not found")

        try:
            # 解密API密钥
            api_key = decrypt_api_key(credential.api_key_encrypted)

            # 创建适配器
            adapter = LLMAdapterFactory.create_adapter(
                provider=credential.provider,
                api_key=api_key,
                api_url=credential.api_url
            )

            # 确定要验证的模型列表
            if credential.custom_models:
                models_to_validate = credential.custom_models
            else:
                # 获取默认模型列表
                models_to_validate = await adapter.get_available_models()

            # 并行验证所有模型
            validation_results = await self._validate_models_parallel(
                adapter, models_to_validate
            )

            # 统计验证结果
            valid_models = [model for model, result in validation_results.items()
                           if result["is_valid"]]
            invalid_models = [model for model, result in validation_results.items()
                             if not result["is_valid"]]

            # 保存详细验证结果到数据库
            credential.model_validation_results = validation_results

            # 更新整体验证状态
            if valid_models:
                credential.is_validated = True
                if invalid_models:
                    credential.validation_error = f"部分模型验证失败: {', '.join(invalid_models)}"
                else:
                    credential.validation_error = None
            else:
                credential.is_validated = False
                credential.validation_error = f"所有模型验证失败: {', '.join(invalid_models)}"

            self.db.commit()
            await adapter.close()

            # 创建验证摘要
            total_tested = len(models_to_validate)
            valid_count = len(valid_models)
            failed_count = len(invalid_models)

            if valid_count == total_tested:
                summary = f"所有 {total_tested} 个模型验证成功"
            elif valid_count > 0:
                summary = f"{valid_count}/{total_tested} 个模型验证成功，{failed_count} 个失败"
            else:
                summary = f"所有 {total_tested} 个模型验证失败"

            return CredentialValidate(
                is_valid=len(valid_models) > 0,
                available_models=valid_models,
                failed_models=invalid_models,
                model_validation_results=validation_results,
                total_models_tested=total_tested,
                validation_summary=summary,
                error_message=credential.validation_error
            )

        except Exception as e:
            logger.error(f"Credential validation error: {e}")

            # 更新验证状态
            credential.is_validated = False
            credential.validation_error = str(e)
            credential.model_validation_results = {}
            self.db.commit()

            return CredentialValidate(
                is_valid=False,
                error_message=str(e)
            )

    async def _validate_models_parallel(self, adapter, models: List[str]) -> Dict[str, Dict]:
        """并行验证多个模型"""
        async def validate_single_model(model_name: str) -> tuple[str, Dict]:
            """验证单个模型"""
            try:
                is_valid = await adapter.validate_model(model_name)
                return model_name, {
                    "is_valid": is_valid,
                    "error": None,
                    "validated_at": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.warning(f"Model {model_name} validation failed: {e}")
                return model_name, {
                    "is_valid": False,
                    "error": str(e),
                    "validated_at": datetime.utcnow().isoformat()
                }

        # 创建并行任务
        tasks = [validate_single_model(model) for model in models]

        # 并行执行验证
        results = await asyncio.gather(*tasks)

        # 转换为字典格式
        return dict(results)

    def mask_api_key(self, api_key_encrypted: str) -> str:
        """遮盖API密钥"""
        try:
            api_key = decrypt_api_key(api_key_encrypted)
            if len(api_key) <= 8:
                return "*" * len(api_key)
            return f"{api_key[:4]}...{api_key[-4:]}"
        except Exception:
            return "***masked***"

    async def get_available_models(self, user: User, credential_id: str) -> List[str]:
        """获取凭证支持的可用模型"""
        credential = self.get_credential_by_id(user, credential_id)
        if not credential:
            raise CredentialValidationError("Credential not found")

        if not credential.is_validated:
            raise CredentialValidationError("Credential is not validated. Please validate the credential first.")

        # 如果用户定义了自定义模型，返回这些模型
        if credential.custom_models:
            return credential.custom_models

        try:
            # 解密API密钥
            api_key = decrypt_api_key(credential.api_key_encrypted)

            # 创建适配器
            adapter = LLMAdapterFactory.create_adapter(
                provider=credential.provider,
                api_key=api_key,
                api_url=credential.api_url
            )

            # 获取适配器的默认可用模型
            models = await adapter.get_available_models()
            await adapter.close()

            return models

        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            raise CredentialValidationError(f"Failed to get available models: {str(e)}")