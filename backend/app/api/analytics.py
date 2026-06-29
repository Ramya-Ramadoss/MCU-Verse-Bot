from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.core.config import settings
from backend.app.db.models.analytics import AnalyticsLog
from backend.app.db.models.conversation import Conversation, Message
from backend.app.db.models.document import Document
from backend.app.db.models.embedding import EmbeddingTrack
from backend.app.db.models.graph import Entity
from backend.app.retrieval.embeddings.faiss_manager import get_faiss_manager

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
def get_analytics(db: Session = Depends(get_db)):
    total_conversations = db.query(func.count(Conversation.id)).scalar() or 0
    total_messages = db.query(func.count(Message.id)).scalar() or 0
    avg_confidence = db.query(func.avg(Message.confidence_score)).filter(
        Message.role == "assistant"
    ).scalar() or 0
    avg_retrieval = db.query(func.avg(AnalyticsLog.retrieval_time_ms)).scalar() or 0
    avg_llm = db.query(func.avg(AnalyticsLog.llm_time_ms)).scalar() or 0
    cache_hits = db.query(func.count(AnalyticsLog.id)).filter(
        AnalyticsLog.is_cache_hit.is_(True)
    ).scalar() or 0
    total_logs = db.query(func.count(AnalyticsLog.id)).scalar() or 0
    embedding_count = db.query(func.count(EmbeddingTrack.id)).scalar() or 0
    document_count = db.query(func.count(Document.id)).scalar() or 0
    entity_count = db.query(func.count(Entity.id)).scalar() or 0

    faiss = get_faiss_manager()
    faiss.load_index()
    index_vectors = faiss.index.ntotal if faiss.index else 0

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "average_confidence": round(float(avg_confidence), 3),
        "average_retrieval_time_ms": round(float(avg_retrieval), 2),
        "average_llm_time_ms": round(float(avg_llm), 2),
        "cache_hit_rate": round(cache_hits / max(total_logs, 1), 3),
        "embedding_count": embedding_count,
        "document_count": document_count,
        "entity_count": entity_count,
        "index_loaded": index_vectors > 0,
        "index_chunks": index_vectors,
        "llm_provider": settings.LLM_PROVIDER,
        "cache_provider": settings.CACHE_PROVIDER,
    }
