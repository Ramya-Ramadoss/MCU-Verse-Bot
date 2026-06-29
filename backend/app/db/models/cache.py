import datetime
from sqlalchemy import Column, String, DateTime, Text
from backend.app.db.database import Base

class CacheEntry(Base):
    __tablename__ = "cache_entries"

    key = Column(String(512), primary_key=True)
    value = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
