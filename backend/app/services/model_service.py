from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.model_config import ModelConfig
from app.models.credential import Credential
from app.models.user import User
from app.schemas.model_config import ModelConfigCreate, ModelConfigUpdate, ModelConfigWithCredential
from app.utils.security import generate_proxy_api_key
from app.exceptions import CredentialValidationError
import logging

logger = logging.getLogger(__name__)


class ModelService:
    def __init__(self, db: Session):
        self.db = db

    def create_model_config(self, user: User, config_data: ModelConfigCreate) -> ModelConfig:
        """创建模型配置"""
        # 验证凭证是否属于当前用户
        credential = self.db.query(Credential).filter(
            and_(
                Credential.id == config_data.credential_id,
                Credential.user_id == user.id
            )
        ).first()

        if not credential:
            raise CredentialValidationError("Credential not found or not accessible")

        # 检查是否已存在相同的模型配置
        existing = self.db.query(ModelConfig).filter(
            and_(
                ModelConfig.credential_id == config_data.credential_id,
                ModelConfig.model_name == config_data.model_name,
                ModelConfig.target_format == config_data.target_format
            )
        ).first()

        if existing:
            raise CredentialValidationError(
                f"Model configuration for '{config_data.model_name}' "
                f"to '{config_data.target_format}' already exists"
            )

        # 生成代理API密钥
        proxy_api_key = generate_proxy_api_key()

        # 创建模型配置
        model_config = ModelConfig(
            credential_id=config_data.credential_id,
            model_name=config_data.model_name,
            target_format=config_data.target_format,
            is_enabled=config_data.is_enabled,
            proxy_api_key=proxy_api_key,
            rate_limit=config_data.rate_limit
        )

        self.db.add(model_config)
        self.db.commit()
        self.db.refresh(model_config)

        return model_config

    def get_user_model_configs(self, user: User) -> List[ModelConfig]:
        """获取用户的所有模型配置"""
        return self.db.query(ModelConfig).join(Credential).filter(
            Credential.user_id == user.id
        ).all()

    def get_model_configs_with_credential(self, user: User) -> List[ModelConfigWithCredential]:
        """获取包含凭证信息的模型配置"""
        configs = self.db.query(ModelConfig, Credential).join(
            Credential, ModelConfig.credential_id == Credential.id
        ).filter(Credential.user_id == user.id).all()

        result = []
        for config, credential in configs:
            config_with_cred = ModelConfigWithCredential(
                id=config.id,
                credential_id=config.credential_id,
                model_name=config.model_name,
                target_format=config.target_format,
                is_enabled=config.is_enabled,
                rate_limit=config.rate_limit,
                proxy_api_key=config.proxy_api_key,
                created_at=config.created_at,
                updated_at=config.updated_at,
                credential_name=credential.name,
                credential_provider=credential.provider
            )
            result.append(config_with_cred)

        return result

    def get_model_config_by_id(self, user: User, config_id: str) -> Optional[ModelConfig]:
        """根据ID获取模型配置"""
        return self.db.query(ModelConfig).join(Credential).filter(
            and_(
                ModelConfig.id == config_id,
                Credential.user_id == user.id
            )
        ).first()

    def get_model_config_by_proxy_key(self, proxy_api_key: str) -> Optional[ModelConfig]:
        """根据代理API密钥获取模型配置"""
        return self.db.query(ModelConfig).filter(
            ModelConfig.proxy_api_key == proxy_api_key
        ).first()

    def update_model_config(self, user: User, config_id: str, update_data: ModelConfigUpdate) -> Optional[ModelConfig]:
        """更新模型配置"""
        config = self.get_model_config_by_id(user, config_id)
        if not config:
            return None

        # 检查是否会产生重复配置
        if update_data.model_name or update_data.target_format:
            model_name = update_data.model_name or config.model_name
            target_format = update_data.target_format or config.target_format

            existing = self.db.query(ModelConfig).filter(
                and_(
                    ModelConfig.credential_id == config.credential_id,
                    ModelConfig.model_name == model_name,
                    ModelConfig.target_format == target_format,
                    ModelConfig.id != config_id
                )
            ).first()

            if existing:
                raise CredentialValidationError(
                    f"Model configuration for '{model_name}' "
                    f"to '{target_format}' already exists"
                )

        # 更新字段
        if update_data.model_name is not None:
            config.model_name = update_data.model_name

        if update_data.target_format is not None:
            config.target_format = update_data.target_format

        if update_data.is_enabled is not None:
            config.is_enabled = update_data.is_enabled

        if update_data.rate_limit is not None:
            config.rate_limit = update_data.rate_limit

        self.db.commit()
        self.db.refresh(config)

        return config

    def delete_model_config(self, user: User, config_id: str) -> bool:
        """删除模型配置"""
        config = self.get_model_config_by_id(user, config_id)
        if not config:
            return False

        self.db.delete(config)
        self.db.commit()
        return True

    def regenerate_proxy_api_key(self, user: User, config_id: str) -> Optional[str]:
        """重新生成代理API密钥"""
        config = self.get_model_config_by_id(user, config_id)
        if not config:
            return None

        new_proxy_key = generate_proxy_api_key()
        config.proxy_api_key = new_proxy_key

        self.db.commit()
        self.db.refresh(config)

        return new_proxy_key

    def get_enabled_configs_by_credential(self, credential_id: str) -> List[ModelConfig]:
        """获取凭证下所有启用的模型配置"""
        return self.db.query(ModelConfig).filter(
            and_(
                ModelConfig.credential_id == credential_id,
                ModelConfig.is_enabled == True
            )
        ).all()

    def validate_model_config_access(self, user: User, config_id: str) -> bool:
        """验证用户是否有权访问模型配置"""
        config = self.db.query(ModelConfig).join(Credential).filter(
            and_(
                ModelConfig.id == config_id,
                Credential.user_id == user.id
            )
        ).first()
        return config is not None