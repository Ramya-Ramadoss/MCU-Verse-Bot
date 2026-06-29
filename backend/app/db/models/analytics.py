import uuid
import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Integer, ForeignKey
from backend.app.db.database import Base

class AnalyticsLog(Base):
    __tablename__ = "analytics_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    api_endpoint = Column(String(255), nullable=False)
    retrieval_time_ms = Column(Float, default=0.0)
    embedding_time_ms = Column(Float, default=0.0)
    llm_time_ms = Column(Float, default=0.0)
    is_cache_hit = Column(Boolean, default=False)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
