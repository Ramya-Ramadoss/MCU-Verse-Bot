from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatSettingsSchema(BaseModel):
    theme: str = "jarvis-blue"
    llm_provider: str = "retrieval_only"
    preferred_model: Optional[str] = None
    temperature: float = 0.7
    top_k: int = 5
    spoiler_preference: str = "full"  # none, partial, full
    watched_up_to_movie: Optional[str] = None
    watched_up_to_series: Optional[str] = None
    language: str = "en"

    model_config = ConfigDict(from_attributes=True)

class ChatMessageCreate(BaseModel):
    content: str
    settings: Optional[ChatSettingsSchema] = None

class CitationSchema(BaseModel):
    source: str
    score: Optional[float] = None
    category: Optional[str] = None
    title: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: Optional[List[CitationSchema]] = None
    confidence_score: float
    provider_used: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    settings: Optional[ChatSettingsSchema] = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    settings: Optional[ChatSettingsSchema] = None

    model_config = ConfigDict(from_attributes=True)
