import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime

from backend.app.api.deps import get_db, get_optional_user
from backend.app.db.models.conversation import Conversation, Message
from backend.app.db.models.user import Settings
from backend.app.db.models.user import User
from backend.app.models.chat import (
    ConversationResponse,
    ConversationCreate,
    ChatMessageCreate,
    ChatMessageResponse,
    CitationSchema,
    ChatSettingsSchema,
)
from backend.app.retrieval.searcher import HybridSearcher
from backend.app.services.llm.providers import get_llm_provider

router = APIRouter()

ANSWER_CACHE_VERSION = "v5"
SEARCHER = HybridSearcher()
SMALLTALK_INPUTS = {
    "hi",
    "hello",
    "hey",
    "yo",
    "good morning",
    "good afternoon",
    "good evening",
}


def _is_smalltalk(text: str) -> bool:
    normalized = text.lower().strip(" .!?,")
    normalized = re.sub(r"[^a-z\s]", "", normalized)
    normalized = re.sub(r"(.)\1{1,}", r"\1", normalized)
    tokens = [token for token in normalized.split() if token not in {"bot", "jarvis", "ai", "mcuverse"}]
    if not tokens:
        return True
    normalized_without_bot = " ".join(tokens)
    if normalized_without_bot in SMALLTALK_INPUTS:
        return True
    greeting_stems = {"hi", "hey", "hello", "yo"}
    return len(tokens) <= 3 and any(
        token in SMALLTALK_INPUTS or any(token.startswith(stem) for stem in greeting_stems)
        for token in tokens
    )


def _smalltalk_response(text: str) -> str:
    return (
        "Hello. I am ready to explore the MCU knowledge base with you. "
        "Ask me about a character, movie, Disney+ series, team, artifact, timeline, or relationship."
    )


def _settings_to_schema(settings: Settings) -> ChatSettingsSchema:
    return ChatSettingsSchema(
        theme=settings.theme or "jarvis-blue",
        llm_provider=settings.llm_provider or "retrieval_only",
        preferred_model=settings.preferred_model,
        temperature=float(settings.temperature) if settings.temperature else 0.7,
        top_k=int(settings.top_k) if settings.top_k and settings.top_k.isdigit() else 5,
        spoiler_preference=settings.spoiler_preference or "full",
        watched_up_to_movie=settings.watched_up_to_movie,
        watched_up_to_series=settings.watched_up_to_series,
        language=settings.language or "en",
    )


def _effective_settings(settings: Settings, request_settings: ChatSettingsSchema | None) -> ChatSettingsSchema:
    base = _settings_to_schema(settings)
    if not request_settings:
        return base

    return ChatSettingsSchema(
        **{
            **base.model_dump(),
            **request_settings.model_dump(exclude_unset=True),
        }
    )


def _cache_key_for_message(content: str, settings: ChatSettingsSchema) -> str:
    key_payload = {
        "content": content,
        "spoiler_preference": settings.spoiler_preference,
        "watched_up_to_movie": settings.watched_up_to_movie,
        "watched_up_to_series": settings.watched_up_to_series,
        "llm_provider": settings.llm_provider,
        "top_k": settings.top_k,
        "continuity_filter": settings.continuity_filter,
        "canon_status_filter": settings.canon_status_filter,
        "universe_filter": settings.universe_filter,
        "earth_filter": settings.earth_filter,
        "knowledge_type_filter": settings.knowledge_type_filter,
    }
    return f"chat:{ANSWER_CACHE_VERSION}:{key_payload}"


def _citation_from_result(result) -> CitationSchema:
    metadata = result.metadata or {}
    return CitationSchema(
        source=metadata.get("file_path", result.document_id),
        score=round(result.score, 3),
        category=result.category,
        title=result.title,
        source_type=result.source_type,
        reason=metadata.get("reason"),
        continuity=metadata.get("continuity"),
        canon_status=metadata.get("canon_status"),
        universe=metadata.get("universe"),
        earth=metadata.get("earth"),
        knowledge_type=metadata.get("knowledge_type"),
        linked_entities=metadata.get("linked_entities"),
    )


def _process_chat(
    db: Session,
    conversation_id: str,
    msg_in: ChatMessageCreate,
    current_user: User | None = None,
) -> ChatMessageResponse:
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Conversation belongs to another user")

    settings = db.query(Settings).filter(Settings.conversation_id == conversation_id).first()
    if not settings:
        in_settings = msg_in.settings or ChatSettingsSchema()
        settings = Settings(
            conversation_id=conversation_id,
            theme=in_settings.theme,
            llm_provider=in_settings.llm_provider,
            preferred_model=in_settings.preferred_model,
            temperature=str(in_settings.temperature),
            top_k=str(in_settings.top_k),
            spoiler_preference=in_settings.spoiler_preference,
            watched_up_to_movie=in_settings.watched_up_to_movie,
            watched_up_to_series=in_settings.watched_up_to_series,
            language=in_settings.language,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    elif msg_in.settings:
        in_settings = msg_in.settings
        settings.llm_provider = in_settings.llm_provider
        settings.spoiler_preference = in_settings.spoiler_preference
        settings.top_k = str(in_settings.top_k)
        db.commit()

    effective_settings = _effective_settings(settings, msg_in.settings)

    if _is_smalltalk(msg_in.content):
        user_msg = Message(conversation_id=conversation_id, role="user", content=msg_in.content)
        db.add(user_msg)
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=_smalltalk_response(msg_in.content),
            citations=[],
            confidence_score=1.0,
            provider_used="retrieval_only",
            prompt_tokens=0,
            completion_tokens=0,
        )
        db.add(assistant_msg)
        if conv.title == "New Conversation" or not conv.title:
            conv.title = "MCUVerse Assistant"
        conv.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(assistant_msg)
        return assistant_msg

    # Check cache first
    from backend.app.services.cache import get_cache
    import json
    
    cache_service = get_cache()
    cache_key = _cache_key_for_message(msg_in.content, effective_settings)
    cached_data = cache_service.get(cache_key)
    
    if cached_data:
        try:
            cached_json = json.loads(cached_data)
            
            # Save user message to DB
            user_msg = Message(conversation_id=conversation_id, role="user", content=msg_in.content)
            db.add(user_msg)
            
            # Save cached assistant response to DB
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=cached_json["content"],
                citations=cached_json["citations"],
                confidence_score=cached_json["confidence_score"],
                provider_used=cached_json["provider_used"],
                prompt_tokens=0,
                completion_tokens=0
            )
            db.add(assistant_msg)
            
            if conv.title == "New Conversation" or not conv.title:
                conv.title = msg_in.content[:60] + ("..." if len(msg_in.content) > 60 else "")
            conv.updated_at = datetime.datetime.utcnow()
            db.commit()
            db.refresh(assistant_msg)
            print(f"Cache hit for key: {cache_key}")
            return assistant_msg
        except Exception as e:
            print(f"Failed to retrieve cached response: {e}")

    # Cache miss - run full pipeline
    user_msg = Message(conversation_id=conversation_id, role="user", content=msg_in.content)
    db.add(user_msg)
    db.commit()

    top_k = effective_settings.top_k or 5
    results, intent = SEARCHER.search(db, msg_in.content, settings=effective_settings, top_k=top_k)

    citations: List[CitationSchema] = []
    for result in results:
        citations.append(_citation_from_result(result))

    has_graph_hit = any(result.source_type == "graph" for result in results)
    best_score = max((result.score for result in results), default=0.0)
    if not results or (best_score < 0.45 and not has_graph_hit):
        llm_content = (
            "I do not have enough relevant MCU knowledge-base evidence to answer that accurately. "
            "Try asking about a specific character, movie, series, team, artifact, or relationship."
        )
        llm_provider = "retrieval_only"
        prompt_tokens = 0
        completion_tokens = 0
    else:
        context = SEARCHER.build_context(results)
        provider = get_llm_provider(effective_settings.llm_provider)
        llm_resp = provider.generate(
            msg_in.content,
            context,
            temperature=effective_settings.temperature,
        )
        llm_content = llm_resp.content
        llm_provider = llm_resp.provider
        prompt_tokens = llm_resp.prompt_tokens
        completion_tokens = llm_resp.completion_tokens

    confidence = min(0.99, max(0.35, sum(result.score for result in results) / max(len(results), 1)))

    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=llm_content,
        citations=[c.model_dump() for c in citations],
        confidence_score=confidence,
        provider_used=llm_provider,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    db.add(assistant_msg)

    # Save to cache
    try:
        cache_data = {
            "content": assistant_msg.content,
            "citations": assistant_msg.citations,
            "confidence_score": assistant_msg.confidence_score,
            "provider_used": assistant_msg.provider_used
        }
        cache_service.set(cache_key, json.dumps(cache_data), expire_seconds=3600)
    except Exception as e:
        print(f"Failed to save response to cache: {e}")

    if conv.title == "New Conversation" or not conv.title:
        conv.title = msg_in.content[:60] + ("..." if len(msg_in.content) > 60 else "")
    conv.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(assistant_msg)
    return assistant_msg


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    query = db.query(Conversation).order_by(Conversation.updated_at.desc())
    if current_user:
        query = query.filter(Conversation.user_id == current_user.id)
    conversations = query.all()
    result = []
    for conv in conversations:
        conv_settings = db.query(Settings).filter(Settings.conversation_id == conv.id).first()
        result.append(
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                settings=_settings_to_schema(conv_settings) if conv_settings else ChatSettingsSchema(),
            )
        )
    return result


@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    conv_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    conv = Conversation(title=conv_in.title or "New Conversation", user_id=current_user.id if current_user else None)
    db.add(conv)
    db.commit()
    db.refresh(conv)

    in_settings = conv_in.settings or ChatSettingsSchema()
    db_settings = Settings(
        conversation_id=conv.id,
        theme=in_settings.theme,
        llm_provider=in_settings.llm_provider,
        preferred_model=in_settings.preferred_model,
        temperature=str(in_settings.temperature),
        top_k=str(in_settings.top_k),
        spoiler_preference=in_settings.spoiler_preference,
        watched_up_to_movie=in_settings.watched_up_to_movie,
        watched_up_to_series=in_settings.watched_up_to_series,
        language=in_settings.language,
    )
    db.add(db_settings)
    db.commit()

    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        settings=in_settings,
    )


@router.delete("/conversations/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conv_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Conversation belongs to another user")
    db.delete(conv)
    db.commit()
    return None


@router.get("/conversations/{conv_id}/messages", response_model=List[ChatMessageResponse])
def get_conversation_messages(
    conv_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Conversation belongs to another user")
    return (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
        .all()
    )


@router.post("/conversations/{conv_id}/messages", response_model=ChatMessageResponse)
def send_message_to_conversation(
    conv_id: str,
    msg_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    return _process_chat(db, conv_id, msg_in, current_user=current_user)


@router.post("/send", response_model=ChatMessageResponse)
def send_message_legacy(
    msg_in: ChatMessageCreate,
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    return _process_chat(db, conversation_id, msg_in, current_user=current_user)
