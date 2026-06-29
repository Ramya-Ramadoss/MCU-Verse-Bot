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
    EntityResponse,
    RelationshipResponse,
    IngestionStatsResponse,
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


@router.get("/relationships", response_model=List[RelationshipResponse])
def list_relationships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Relationship).offset(skip).limit(limit).all()
