from backend.app.db.models.document import Document
from backend.app.retrieval.searcher import (
    HybridSearcher,
    hybrid_search_documents,
    link_query_entities,
    search_documents_fts,
    search_knowledge_graph,
)


def test_knowledge_graph_mentor_query(db_session, knowledge_dir):
    from backend.app.services.knowledge.ingestion import ingest_all_knowledge

    ingest_all_knowledge(db_session, knowledge_dir)
    results = search_knowledge_graph("Who mentored Spider-Man?", db_session)
    assert len(results) >= 1
    assert any("mentored" in r["relation"] for r in results)


def test_entity_linking_matches_aliases(db_session, knowledge_dir):
    from backend.app.services.knowledge.ingestion import ingest_all_knowledge

    ingest_all_knowledge(db_session, knowledge_dir)
    linked = link_query_entities("Tell me about Iron Man", db_session)

    assert any(entity.id == "tony_stark" for entity in linked)


def test_metadata_filters_limit_keyword_results(db_session):
    comics_doc = Document(
        title="Secret Wars (2015)",
        category="comic_events",
        content="Doctor Doom and Battleworld are central to Secret Wars comics context.",
        metadata_json={
            "knowledge_type": "comic_event",
            "continuity": "comics",
            "canon_status": "mainline_comics",
            "spoiler_level": "partial",
        },
    )
    mcu_doc = Document(
        title="MCU Secret Wars Future Project",
        category="movies",
        content="Secret Wars is represented here as future MCU project context.",
        metadata_json={
            "knowledge_type": "movie",
            "continuity": "mcu",
            "canon_status": "official_confirmation",
            "spoiler_level": "none",
        },
    )
    db_session.add_all([comics_doc, mcu_doc])
    db_session.commit()

    class MockSettings:
        spoiler_preference = "full"
        watched_up_to_movie = None
        continuity_filter = "comics"
        canon_status_filter = None
        universe_filter = None
        earth_filter = None
        knowledge_type_filter = "comic_event"

    results = search_documents_fts("Secret Wars", MockSettings(), db_session)

    assert [doc.title for doc in results] == ["Secret Wars (2015)"]


def test_hybrid_search_returns_documents(db_session, knowledge_dir):
    from backend.app.services.knowledge.ingestion import ingest_all_knowledge

    ingest_all_knowledge(db_session, knowledge_dir)
    results = hybrid_search_documents("Tony Stark Iron Man", None, db_session, top_k=3)
    assert len(results) >= 1
    titles = [doc.title for doc, _ in results]
    assert any("Tony" in t or "Iron" in t for t in titles)


def test_hybrid_searcher_returns_graph_context(db_session, knowledge_dir):
    from backend.app.services.knowledge.ingestion import ingest_all_knowledge

    ingest_all_knowledge(db_session, knowledge_dir)
    searcher = HybridSearcher()
    results, intent = searcher.search(db_session, "Who mentored Spider-Man?", top_k=5)

    assert intent == "relationship"
    assert any(result.source_type == "graph" for result in results)
    context = searcher.build_context(results)
    assert "Tony Stark" in context
    assert "Peter Parker" in context
