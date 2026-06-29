# Import all models here so that they are registered on the Base
from backend.app.db.database import Base
from backend.app.db.models.user import User, Settings
from backend.app.db.models.conversation import Conversation, Message
from backend.app.db.models.document import Document
from backend.app.db.models.graph import Entity, Relationship
from backend.app.db.models.embedding import EmbeddingTrack
from backend.app.db.models.analytics import AnalyticsLog
from backend.app.db.models.cache import CacheEntry
