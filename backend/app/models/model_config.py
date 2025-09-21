import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id = Column(String(36), ForeignKey("credentials.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(100), nullable=False)
    target_format = Column(String(50), nullable=False)  # 'openai', 'anthropic'
    is_enabled = Column(Boolean, default=True)
    proxy_api_key = Column(String(255), nullable=False)  # 用于访问转发服务的密钥
    rate_limit = Column(Integer, default=100)  # 每分钟请求限制
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    credential = relationship("Credential", back_populates="model_configs")
    request_logs = relationship("RequestLog", back_populates="model_config", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ModelConfig(id={self.id}, model_name={self.model_name}, target_format={self.target_format})>"