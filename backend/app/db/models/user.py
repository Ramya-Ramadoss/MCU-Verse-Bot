import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth/Guest users
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="user")  # "admin", "user", "guest"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    settings = relationship("Settings", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class Settings(Base):
    __tablename__ = "settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, unique=True)
    
    theme = Column(String(50), default="jarvis-blue")  # jarvis-blue, dark, light
    llm_provider = Column(String(50), default="retrieval_only")  # gemini, openai, anthropic, groq, ollama, retrieval_only
    preferred_model = Column(String(100), nullable=True)
    temperature = Column(String(10), default="0.7")  # stored as string to easily handle precision or customize
    top_k = Column(String(10), default="5")
    spoiler_preference = Column(String(50), default="full")  # none, partial, full
    watched_up_to_movie = Column(String(255), nullable=True)
    watched_up_to_series = Column(String(255), nullable=True)
    language = Column(String(50), default="en")

    user = relationship("User", back_populates="settings")
    conversation = relationship("Conversation", back_populates="settings")
