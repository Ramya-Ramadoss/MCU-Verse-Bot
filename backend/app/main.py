from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import analytics, auth, chat, knowledge
from backend.app.core.config import settings
from backend.app.db.database import SessionLocal
from backend.app.db.init_db import init_db
from backend.app.db.models.document import Document
from backend.app.retrieval.embeddings.faiss_manager import get_faiss_manager
from backend.app.services.knowledge.ingestion import ingest_all_knowledge


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up MCUVerse AI Backend...")
    init_db()

    db = SessionLocal()
    try:
        knowledge_dir = os.path.join(_project_root(), "knowledge")
        if db.query(Document).count() == 0 and os.path.isdir(knowledge_dir):
            print(f"Ingesting knowledge from {knowledge_dir}...")
            ingest_all_knowledge(db, knowledge_dir)

        faiss = get_faiss_manager()
        faiss.load_index()
        if faiss.index is None or faiss.index.ntotal == 0:
            if db.query(Document).count() > 0:
                print("Building FAISS index...")
                faiss.rebuild_index(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(knowledge.router, prefix=f"{settings.API_V1_STR}/knowledge", tags=["knowledge"])
app.include_router(analytics.router, prefix=settings.API_V1_STR, tags=["analytics"])
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["auth"])


@app.get("/health")
@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    faiss = get_faiss_manager()
    faiss.load_index()
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "llm_provider": settings.LLM_PROVIDER,
        "cache_provider": settings.CACHE_PROVIDER,
        "index_vectors": faiss.index.ntotal if faiss.index else 0,
    }


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
    }
