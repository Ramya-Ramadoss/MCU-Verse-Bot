import uuid
from sqlalchemy import Column, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.db.database import Base

class Entity(Base):
    __tablename__ = "entities"

    id = Column(String(100), primary_key=True)  # unique string ID, e.g., 'tony_stark'
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)  # character, team, movie, artifact, location
    aliases_json = Column(JSON, nullable=True)  # store aliases as a list
    description = Column(Text, nullable=True)

    # Relationships as source
    relations_out = relationship(
        "Relationship",
        foreign_keys="[Relationship.source_entity_id]",
        back_populates="source_entity",
        cascade="all, delete-orphan"
    )
    # Relationships as target
    relations_in = relationship(
        "Relationship",
        foreign_keys="[Relationship.target_entity_id]",
        back_populates="target_entity",
        cascade="all, delete-orphan"
    )

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_entity_id = Column(String(100), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id = Column(String(100), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(100), nullable=False, index=True)  # mentored, member_of, brother_of, creator_of
    description = Column(Text, nullable=True)

    source_entity = relationship("Entity", foreign_keys=[source_entity_id], back_populates="relations_out")
    target_entity = relationship("Entity", foreign_keys=[target_entity_id], back_populates="relations_in")
