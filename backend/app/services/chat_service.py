import time
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.app.db.models.analytics import AnalyticsLog
from backend.app.db.models.conversation import Conversation, Message
from backend.app.models.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSettingsSchema,
    CitationSchema,
    ConversationCreate,
    ConversationResponse,
)
from backend.app.retrieval.searcher import HybridSearcher
from backend.app.services.cache.service import CacheService
from backend.app.services.llm.providers import get_llm_provider


class ChatService:
    def __init__(self) -> None:
        self.searcher = HybridSearcher()
        self.cache = CacheService()

    def create_conversation(
        self, db: Session, payload: ConversationCreate, user_id: Optional[str] = None
    ) -> Conversation:
        conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=payload.title or "New Conversation",
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    def get_conversations(self, db: Session, user_id: Optional[str] = None) -> List[Conversation]:
        q = db.query(Conversation).order_by(Conversation.updated_at.desc())
        if user_id:
            q = q.filter(Conversation.user_id == user_id)
        return q.limit(50).all()

    def get_messages(self, db: Session, conversation_id: str) -> List[Message]:
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    def delete_conversation(self, db: Session, conversation_id: str) -> bool:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return False
        db.delete(conv)
        db.commit()
        return True

    def process_message(
        self,
        db: Session,
        conversation_id: str,
        payload: ChatMessageCreate,
    ) -> ChatMessageResponse:
        start = time.time()
        settings = payload.settings or ChatSettingsSchema()
        top_k = settings.top_k or 5

        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise ValueError("Conversation not found")

        user_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=payload.content,
        )
        db.add(user_msg)

        cache_key = CacheService.make_key(
            "chat",
            {"q": payload.content, "settings": settings.model_dump(), "top_k": top_k},
        )
        cached = self.cache.get(cache_key)
        if cached:
            assistant = Message(**cached)
            assistant.id = str(uuid.uuid4())
            assistant.conversation_id = conversation_id
            db.add(assistant)
            db.commit()
            return self._to_response(assistant)

        retrieval_start = time.time()
        results, intent = self.searcher.search(db, payload.content, settings=settings, top_k=top_k)
        retrieval_ms = (time.time() - retrieval_start) * 1000

        context = self.searcher.build_context(results)
        provider = get_llm_provider(settings.llm_provider)
        llm_start = time.time()
        llm_resp = provider.generate(payload.content, context, temperature=settings.temperature)
        llm_ms = (time.time() - llm_start) * 1000

        citations = [
            CitationSchema(
                source=r.document_id,
                score=round(r.score, 3),
                category=r.category,
                title=r.title,
            ).model_dump()
            for r in results
        ]

        confidence = min(0.99, max(0.3, sum(r.score for r in results) / max(len(results), 1)))

        assistant = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content=llm_resp.content,
            citations=citations,
            confidence_score=confidence,
            provider_used=llm_resp.provider,
            prompt_tokens=llm_resp.prompt_tokens,
            completion_tokens=llm_resp.completion_tokens,
        )
        db.add(assistant)

        if not conv.title or conv.title == "New Conversation":
            conv.title = payload.content[:60] + ("..." if len(payload.content) > 60 else "")

        log = AnalyticsLog(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            api_endpoint="/chat",
            retrieval_time_ms=retrieval_ms,
            llm_time_ms=llm_ms,
            is_cache_hit=False,
            tokens_used=llm_resp.prompt_tokens + llm_resp.completion_tokens,
        )
        db.add(log)
        db.commit()
        db.refresh(assistant)

        cache_payload = {
            "role": "assistant",
            "content": llm_resp.content,
            "citations": citations,
            "confidence_score": confidence,
            "provider_used": llm_resp.provider,
            "prompt_tokens": llm_resp.prompt_tokens,
            "completion_tokens": llm_resp.completion_tokens,
        }
        self.cache.set(cache_key, cache_payload, ttl_seconds=1800)

        return self._to_response(assistant)

    def _to_response(self, msg: Message) -> ChatMessageResponse:
        citations = None
        if msg.citations:
            citations = [CitationSchema(**c) if isinstance(c, dict) else c for c in msg.citations]
        return ChatMessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            citations=citations,
            confidence_score=msg.confidence_score or 0.0,
            provider_used=msg.provider_used or "retrieval_only",
            created_at=msg.created_at,
        )

    def conversation_to_response(self, conv: Conversation) -> ConversationResponse:
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )
