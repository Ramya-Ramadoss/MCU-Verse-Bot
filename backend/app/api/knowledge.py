from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os

from backend.app.api.deps import get_db, require_admin
from backend.app.db.models.user import User
from backend.app.db.models.document import Document
from backend.app.db.models.graph import Entity, Relationship
from backend.app.models.knowledge import (
    DocumentResponse,
    EntityGraphResponse,
    EntityResponse,
    GraphEdgeResponse,
    GraphNodeResponse,
    RelationshipResponse,
    IngestionStatsResponse,
    TimelineEntryResponse,
)
from backend.app.retrieval.embeddings.faiss_manager import get_faiss_manager
from backend.app.services.knowledge.ingestion import ingest_all_knowledge

router = APIRouter()


def _knowledge_dir() -> str:
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "knowledge")
    )


@router.post("/ingest", response_model=IngestionStatsResponse, status_code=status.HTTP_201_CREATED)
def trigger_ingestion(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    try:
        stats = ingest_all_knowledge(db, _knowledge_dir())
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest knowledge: {str(e)}")


@router.post("/reindex")
def reindex_embeddings(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    faiss = get_faiss_manager()
    chunks = faiss.rebuild_index(db)
    return {"status": "ok", "chunks": chunks}


@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Document).offset(skip).limit(limit).all()


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return doc


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"status": "deleted", "id": doc_id}


@router.get("/entities", response_model=List[EntityResponse])
def list_entities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Entity).offset(skip).limit(limit).all()


@router.get("/entities/{entity_id}/graph", response_model=EntityGraphResponse)
def get_entity_graph(entity_id: str, depth: int = 1, limit: int = 40, db: Session = Depends(get_db)):
    center = db.query(Entity).filter(Entity.id == entity_id).first()
    if not center:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found.")

    depth = max(1, min(depth, 2))
    limit = max(1, min(limit, 100))
    nodes = {center.id: center}
    edges: list[GraphEdgeResponse] = []
    frontier = {center.id}
    visited = set()

    for _ in range(depth):
        if len(edges) >= limit:
            break
        visited.update(frontier)
        rels = (
            db.query(Relationship)
            .filter(
                (Relationship.source_entity_id.in_(frontier))
                | (Relationship.target_entity_id.in_(frontier))
            )
            .limit(limit - len(edges))
            .all()
        )
        next_frontier = set()
        for rel in rels:
            nodes[rel.source_entity_id] = rel.source_entity
            nodes[rel.target_entity_id] = rel.target_entity
            if rel.source_entity_id in frontier:
                direction = "outgoing"
                next_frontier.add(rel.target_entity_id)
            else:
                direction = "incoming"
                next_frontier.add(rel.source_entity_id)
            edges.append(
                GraphEdgeResponse(
                    id=rel.id,
                    source_entity_id=rel.source_entity_id,
                    source_name=rel.source_entity.name,
                    target_entity_id=rel.target_entity_id,
                    target_name=rel.target_entity.name,
                    relation_type=rel.relation_type,
                    description=rel.description,
                    direction=direction,
                )
            )
        frontier = next_frontier - visited
        if not frontier:
            break

    return EntityGraphResponse(
        center=GraphNodeResponse(id=center.id, name=center.name, type=center.type),
        nodes=[
            GraphNodeResponse(id=node.id, name=node.name, type=node.type)
            for node in sorted(nodes.values(), key=lambda item: item.name)
        ],
        edges=edges,
    )


@router.get("/relationships", response_model=List[RelationshipResponse])
def list_relationships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Relationship).offset(skip).limit(limit).all()


@router.get("/timeline", response_model=List[TimelineEntryResponse])
def list_timeline(
    continuity: str | None = None,
    category: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    docs = db.query(Document).all()
    entries = []
    for doc in docs:
        metadata = doc.metadata_json or {}
        if continuity and str(metadata.get("continuity", "")).lower() != continuity.lower():
            continue
        if category and doc.category != category:
            continue

        timeline_position = metadata.get("timeline_position") or {}
        release_order = timeline_position.get("release_order")
        chronological_order = timeline_position.get("chronological_order")
        release_date = metadata.get("release_date")
        chronological_year = metadata.get("chronological_year")
        if not any([release_date, chronological_year, release_order, chronological_order]):
            continue

        entries.append(
            TimelineEntryResponse(
                id=doc.id,
                title=doc.title,
                category=doc.category,
                knowledge_type=metadata.get("knowledge_type"),
                continuity=metadata.get("continuity"),
                release_date=release_date,
                chronological_year=chronological_year,
                release_order=release_order,
                chronological_order=chronological_order,
                spoiler_level=metadata.get("spoiler_level"),
            )
        )

    entries.sort(
        key=lambda entry: (
            entry.chronological_order if entry.chronological_order is not None else 9999,
            entry.release_order if entry.release_order is not None else 9999,
            entry.release_date or "",
            entry.title,
        )
    )
    return entries[: max(1, min(limit, 250))]
