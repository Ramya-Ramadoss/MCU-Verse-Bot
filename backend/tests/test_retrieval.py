from backend.app.retrieval.searcher import HybridSearcher, search_knowledge_graph, hybrid_search_documents


def test_knowledge_graph_mentor_query(db_session, knowledge_dir):
    from backend.app.services.knowledge.ingestion import ingest_all_knowledge

    ingest_all_knowledge(db_session, knowledge_dir)
    results = search_knowledge_graph("Who mentored Spider-Man?", db_session)
    assert len(results) >= 1
    assert any("mentored" in r["relation"] for r in results)


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
