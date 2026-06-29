import uuid
import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Integer, JSON
from sqlalchemy.orm import relationship
from backend.app.db.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # Nullable for guest
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    settings = relationship("Settings", back_populates="conversation", uselist=False, cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # "user", "assistant"
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)  # Store list of citations: [{source, score, character, movie}]
    confidence_score = Column(Float, default=1.0)
    provider_used = Column(String(50), default="retrieval_only")
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
