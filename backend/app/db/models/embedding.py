import uuid
import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from backend.app.db.database import Base

class EmbeddingTrack(Base):
    __tablename__ = "embedding_tracks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False, default=0)
    faiss_index_pos = Column(Integer, nullable=True)  # maps directly to FAISS vector row index
    embedding_model = Column(String(100), nullable=False)
    embedding_version = Column(String(50), nullable=False, default="1.0")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="embeddings")
