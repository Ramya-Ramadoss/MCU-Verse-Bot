from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class DocumentResponse(BaseModel):
    id: str
    title: str
    category: str
    file_path: Optional[str]
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EntityResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class RelationshipResponse(BaseModel):
    id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class GraphNodeResponse(BaseModel):
    id: str
    name: str
    type: str


class GraphEdgeResponse(BaseModel):
    id: str
    source_entity_id: str
    source_name: str
    target_entity_id: str
    target_name: str
    relation_type: str
    description: Optional[str]
    direction: str


class EntityGraphResponse(BaseModel):
    center: GraphNodeResponse
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]


class TimelineEntryResponse(BaseModel):
    id: str
    title: str
    category: str
    knowledge_type: Optional[str] = None
    continuity: Optional[str] = None
    release_date: Optional[str] = None
    chronological_year: Optional[int] = None
    release_order: Optional[int] = None
    chronological_order: Optional[int] = None
    spoiler_level: Optional[str] = None


class IngestionStatsResponse(BaseModel):
    documents: int
    entities: int
    relationships: int
