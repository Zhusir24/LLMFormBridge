import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Credential(Base):
    __tablename__ = "credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)  # 'openai', 'anthropic'
    api_key_encrypted = Column(Text, nullable=False)
    api_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)
    validation_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="credentials")
    model_configs = relationship("ModelConfig", back_populates="credential", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Credential(id={self.id}, name={self.name}, provider={self.provider})>"