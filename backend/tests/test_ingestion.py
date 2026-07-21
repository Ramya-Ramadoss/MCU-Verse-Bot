import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.database import Base
from backend.app.db.models.document import Document
from backend.app.db.models.graph import Entity, Relationship
from backend.app.services.knowledge.ingestion import ingest_all_knowledge
from backend.app.retrieval.searcher import search_documents_fts, search_knowledge_graph
from backend.app.db.init_db import init_db

# Setup test DB
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(name="db_session")
def fixture_db_session():
    # Create test engine
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Register tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize SQLite FTS5 table and triggers on the in-memory database
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                document_id UNINDEXED,
                title,
                content,
                tokenize='porter'
            );
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS trg_documents_after_insert 
            AFTER INSERT ON documents 
            BEGIN
                INSERT INTO documents_fts(document_id, title, content) 
                VALUES (new.id, new.title, new.content);
            END;
        """))
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_knowledge_ingestion_and_search(db_session):
    # Ingest from actual knowledge directory
    # The tests run in backend/ directory or root. Let's make sure it finds the path.
    # Root contains knowledge/
    stats = ingest_all_knowledge(db_session, "knowledge")
    
    assert stats["documents"] > 0
    assert stats["entities"] > 0
    assert stats["relationships"] > 0
    
    # Verify documents exist
    tony = db_session.query(Entity).filter(Entity.id == "tony_stark").first()
    assert tony is not None
    assert tony.name == "Tony Stark"
    
    # Verify relationship exists
    rel = db_session.query(Relationship).filter(
        Relationship.source_entity_id == "tony_stark",
        Relationship.target_entity_id == "peter_parker"
    ).first()
    assert rel is not None
    assert rel.relation_type == "mentored"

    # Test FTS Search (simulate settings object)
    class MockSettings:
        spoiler_preference = "full"
        watched_up_to_movie = None
        
    settings = MockSettings()
    
    # Query FTS5 for "Stark"
    search_results = search_documents_fts("Stark", settings, db_session)
    assert len(search_results) > 0
    assert any("Tony Stark" in doc.title for doc in search_results)

    # Test Relationship Graph Search
    kg_results = search_knowledge_graph("Who mentored Spider-Man?", db_session)
    assert len(kg_results) > 0
    assert kg_results[0]["source"] == "Tony Stark"
    assert kg_results[0]["target"] == "Peter Parker"
    assert kg_results[0]["relation"] == "mentored"

    timeline = db_session.query(Document).filter(
        Document.title == "MCU Chronological Timeline (Selected)"
    ).first()
    assert timeline is not None
    assert timeline.metadata_json["spoiler_level"] == "partial"


def test_modular_knowledge_schema_supports_variants_events_and_embedded_relationships(db_session, tmp_path):
    knowledge_root = tmp_path / "knowledge"
    variants_dir = knowledge_root / "variants"
    events_dir = knowledge_root / "comic_events"
    variants_dir.mkdir(parents=True)
    events_dir.mkdir(parents=True)

    (variants_dir / "sylvie.yaml").write_text(
        """
id: "sylvie_laufeydottir"
name: "Sylvie Laufeydottir"
type: "variant"
continuity: "mcu"
canon_status: "canon"
universe: "branched_timeline"
summary: "A Loki variant connected to TVA branch timeline stories."
variant_of: "loki_laufeyson"
relationships:
  - target_id: "tva"
    relation_type: "enemy_of"
    description: "Sylvie was hunted by the TVA."
""".strip(),
        encoding="utf-8",
    )

    (events_dir / "secret_wars_2015.yaml").write_text(
        """
id: "secret_wars_2015"
title: "Secret Wars (2015)"
type: "comic_event"
continuity: "comics"
canon_status: "mainline_comics"
summary: "A major Marvel Comics event useful for comics-continuity answers."
metadata:
  spoiler_level: "partial"
relationships:
  - target_id: "doctor_doom"
    relation_type: "features"
    description: "Doctor Doom is central to the event context in this local entry."
""".strip(),
        encoding="utf-8",
    )

    stats = ingest_all_knowledge(db_session, str(knowledge_root))

    assert stats["documents"] == 2
    assert stats["relationships"] == 3

    sylvie = db_session.query(Entity).filter(Entity.id == "sylvie_laufeydottir").first()
    assert sylvie is not None
    assert sylvie.type == "variant"

    secret_wars = db_session.query(Document).filter(Document.title == "Secret Wars (2015)").first()
    assert secret_wars is not None
    assert secret_wars.metadata_json["knowledge_type"] == "comic_event"
    assert secret_wars.metadata_json["continuity"] == "comics"
    assert secret_wars.metadata_json["spoiler_level"] == "partial"

    variant_edge = db_session.query(Relationship).filter(
        Relationship.source_entity_id == "sylvie_laufeydottir",
        Relationship.target_entity_id == "loki_laufeyson",
        Relationship.relation_type == "variant_of",
    ).first()
    assert variant_edge is not None

    doom_stub = db_session.query(Entity).filter(Entity.id == "doctor_doom").first()
    assert doom_stub is not None

def test_faiss_and_hybrid_search(db_session):
    from backend.app.retrieval.embeddings.faiss_manager import get_faiss_manager
    from backend.app.retrieval.searcher import hybrid_search_documents
    
    # Ingest docs
    ingest_all_knowledge(db_session, "knowledge")
    
    # Rebuild index (uses SentenceTransformers locally)
    faiss_mgr = get_faiss_manager()
    chunks_indexed = faiss_mgr.rebuild_index(db_session)
    assert chunks_indexed > 0
    
    class MockSettings:
        spoiler_preference = "full"
        watched_up_to_movie = None
        top_k = "5"
        
    settings = MockSettings()
    
    # Hybrid search
    results = hybrid_search_documents("Tony Stark", settings, db_session, top_k=5)
    assert len(results) > 0
    doc, score = results[0]
    assert score > 0.0
    assert doc.title is not None
