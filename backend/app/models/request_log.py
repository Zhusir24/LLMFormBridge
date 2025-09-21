import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_config_id = Column(String(36), ForeignKey("model_configs.id"), nullable=False)
    request_id = Column(String(100))
    method = Column(String(10))
    path = Column(Text)
    source_format = Column(String(50))
    target_format = Column(String(50))
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    model_config = relationship("ModelConfig", back_populates="request_logs")

    def __repr__(self):
        return f"<RequestLog(id={self.id}, request_id={self.request_id}, status_code={self.status_code})>"