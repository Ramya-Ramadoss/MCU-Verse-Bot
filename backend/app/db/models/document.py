import uuid
import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.db.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)  # movies, characters, teams, etc.
    file_path = Column(String(512), nullable=True)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)  # Release date, spoiler level, aliases, phase
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    embeddings = relationship("EmbeddingTrack", back_populates="document", cascade="all, delete-orphan")
