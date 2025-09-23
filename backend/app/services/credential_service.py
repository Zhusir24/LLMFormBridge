from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.credential import Credential
from app.models.user import User
from app.schemas.credential import CredentialCreate, CredentialUpdate, CredentialValidate
from app.utils.security import encrypt_api_key, decrypt_api_key
from app.adapters.factory import LLMAdapterFactory
from app.exceptions import CredentialValidationError
import logging

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
        """验证凭证"""
        credential = self.get_credential_by_id(user, credential_id)
        if not credential:
            raise CredentialValidationError("Credential not found")

        try:
            # 解密API密钥
            api_key = decrypt_api_key(credential.api_key_encrypted)

            # 创建适配器并验证
            adapter = LLMAdapterFactory.create_adapter(
                provider=credential.provider,
                api_key=api_key,
                api_url=credential.api_url
            )

            # 如果用户定义了自定义模型，则验证这些模型
            if credential.custom_models:
                valid_models = []
                invalid_models = []

                for model in credential.custom_models:
                    try:
                        # 使用适配器的内置验证方法验证每个模型
                        is_model_valid = await adapter.validate_model(model)
                        if is_model_valid:
                            valid_models.append(model)
                        else:
                            invalid_models.append(model)
                    except Exception as model_error:
                        logger.warning(f"Model {model} validation failed: {model_error}")
                        invalid_models.append(model)

                if valid_models:
                    # 至少有一个模型可用
                    credential.is_validated = True
                    credential.validation_error = None
                    if invalid_models:
                        credential.validation_error = f"Some models failed: {', '.join(invalid_models)}"
                    self.db.commit()

                    await adapter.close()

                    return CredentialValidate(
                        is_valid=True,
                        available_models=valid_models
                    )
                else:
                    # 所有自定义模型都无法使用
                    credential.is_validated = False
                    credential.validation_error = f"All custom models failed: {', '.join(invalid_models)}"
                    self.db.commit()

                    await adapter.close()

                    return CredentialValidate(
                        is_valid=False,
                        error_message=f"All custom models failed: {', '.join(invalid_models)}"
                    )
            else:
                # 没有自定义模型，使用默认验证
                is_valid = await adapter.validate_credentials()

                if is_valid:
                    # 获取可用模型
                    available_models = await adapter.get_available_models()

                    # 更新验证状态
                    credential.is_validated = True
                    credential.validation_error = None
                    self.db.commit()

                    await adapter.close()

                    return CredentialValidate(
                        is_valid=True,
                        available_models=available_models
                    )
                else:
                    # 更新验证状态
                    credential.is_validated = False
                    credential.validation_error = "Invalid credentials"
                    self.db.commit()

                    await adapter.close()

                    return CredentialValidate(
                        is_valid=False,
                        error_message="Invalid credentials"
                    )

        except Exception as e:
            logger.error(f"Credential validation error: {e}")

            # 更新验证状态
            credential.is_validated = False
            credential.validation_error = str(e)
            self.db.commit()

            return CredentialValidate(
                is_valid=False,
                error_message=str(e)
            )

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