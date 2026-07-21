import re
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Tuple
import json
from backend.app.db.models.document import Document
from backend.app.db.models.graph import Entity, Relationship
from backend.app.retrieval.models import RetrievalResult
from backend.app.retrieval.reranking.ranker import rerank_results
from backend.app.services.knowledge.schema import normalize_entity_id


RELATION_KEYWORDS = {
    "mentored": {"mentor", "mentored", "trained", "trained by", "teacher"},
    "protege_of": {"protege", "student", "trained by"},
    "member_of": {"member", "join", "joined", "part of", "avenger"},
    "enemy_of": {"enemy", "fight", "fought", "foe", "villain", "against"},
    "ally_of": {"ally", "allied", "worked with", "team up", "helped"},
    "possesses": {"possess", "possesses", "wield", "wielder", "uses", "used"},
    "uses": {"use", "uses", "used", "weapon", "technology"},
    "created": {"created", "built", "made", "invented"},
    "leads": {"lead", "leads", "leader"},
    "works_for": {"works for", "agent of", "serves"},
    "sibling_of": {"brother", "sister", "sibling"},
    "parent_of": {"parent", "father", "mother"},
    "child_of": {"child", "son", "daughter"},
    "variant_of": {"variant", "alternate"},
    "appears_in": {"appear", "appears", "appearance", "in both"},
    "introduced_in": {"introduced", "first appeared", "debut"},
    "located_in": {"located", "where", "place"},
}


def detect_intent(query: str) -> str:
    query_lower = query.lower()
    if any(word in query_lower for word in ["timeline", "before", "after", "between", "when"]):
        return "timeline"
    if any(word in query_lower for word in ["mentor", "trained", "member", "enemy", "fought", "wielder", "possess"]):
        return "relationship"
    if any(word in query_lower for word in ["who is", "profile", "bio", "powers", "status"]):
        return "entity_profile"
    return "general"


def expand_query(query: str) -> List[str]:
    expansions = [query]
    query_lower = query.lower()
    aliases = {
        "iron man": "Tony Stark",
        "spider-man": "Peter Parker",
        "spiderman": "Peter Parker",
        "infinity gauntlet": "Infinity Stones Thanos",
        "snap": "Blip Infinity War Endgame",
        "tesseract": "Space Stone",
        "blackpanther": "Black Panther T'Challa Wakanda Shuri Killmonger",
        "black panther": "T'Challa Shuri Wakanda Killmonger Namor",
        "ant man": "Scott Lang Ant-Man Pym Quantum Realm Time Heist",
        "ant-man": "Scott Lang Ant-Man Pym Quantum Realm Time Heist",
        "loki": "Loki TVA Sylvie Mobius variant timeline",
        "moonknight": "Moon Knight Marc Spector Steven Grant Khonshu Layla",
        "moon knight": "Marc Spector Steven Grant Moon Knight Khonshu",
        "gotg": "Guardians of the Galaxy Star-Lord Gamora Rocket Groot Drax",
        "guardians": "Guardians of the Galaxy Star-Lord Gamora Rocket Groot Drax",
        "star lord": "Peter Quill Star-Lord Guardians of the Galaxy",
        "xmen": "X-Men mutants Wolverine Charles Xavier Deadpool",
        "x-men": "X-Men mutants Wolverine Charles Xavier Deadpool",
        "dead pool": "Deadpool Wade Wilson Wolverine X-Men",
        "deadpool": "Deadpool Wade Wilson Wolverine X-Men",
        "wolverine": "Wolverine Logan X-Men Deadpool",
        "eternals": "Eternals Sersi Ikaris Thena Celestials Emergence",
        "ms marvel": "Kamala Khan Ms. Marvel mutation bangle",
        "agent carter": "Peggy Carter SSR S.H.I.E.L.D. Steve Rogers",
    }
    for phrase, expansion in aliases.items():
        if phrase in query_lower and expansion not in expansions:
            expansions.append(expansion)
    return expansions


def link_query_entities(query: str, db: Session) -> List[Entity]:
    """
    Links query text to known entities by id, display name, and aliases.
    Longest names naturally win because all matches are returned and reranking
    can use the complete linked set for boosts and graph traversal.
    """
    query_lower = query.lower()
    normalized_query = normalize_entity_id(query)
    linked: Dict[str, Entity] = {}

    for ent in db.query(Entity).all():
        candidates = [ent.id, ent.name, *(ent.aliases_json or [])]
        for candidate in candidates:
            candidate_lower = str(candidate).lower()
            candidate_id = normalize_entity_id(str(candidate))
            if candidate_lower in query_lower or candidate_id in normalized_query:
                linked[ent.id] = ent
                break

    return sorted(linked.values(), key=lambda ent: len(ent.name), reverse=True)


def metadata_matches_filters(doc_metadata: Dict[str, Any], settings: Any) -> bool:
    if not settings:
        return True

    filter_map = {
        "continuity_filter": "continuity",
        "canon_status_filter": "canon_status",
        "universe_filter": "universe",
        "earth_filter": "earth",
        "knowledge_type_filter": "knowledge_type",
    }
    for setting_name, metadata_key in filter_map.items():
        expected = getattr(settings, setting_name, None)
        if not expected:
            continue
        actual = doc_metadata.get(metadata_key)
        if actual is None:
            return False
        if str(actual).lower() != str(expected).lower():
            return False
    return True


def check_spoiler_filter(doc_metadata: Dict[str, Any], settings: Any, db: Session) -> bool:
    """
    Returns True if the document is allowed under the current user settings,
    False if it should be filtered out due to spoilers.
    """
    if not settings:
        return True
        
    pref = settings.spoiler_preference or "none"
    if pref == "full":
        return True

    # 1. Check basic levels
    doc_level = doc_metadata.get("spoiler_level", "none")
    if pref == "none" and doc_level in ["partial", "full"]:
        return False
    if pref == "partial" and doc_level == "full":
        return False

    # 2. Check Custom Movie Cutoff
    cutoff_movie = settings.watched_up_to_movie
    if cutoff_movie:
        # Find the release date/index of the cutoff movie
        cutoff_doc = db.query(Document).filter(
            Document.category == "movies",
            (Document.title.ilike(f"%{cutoff_movie}%")) | (Document.id == cutoff_movie)
        ).first()
        
        if cutoff_doc and cutoff_doc.metadata_json:
            cutoff_date = cutoff_doc.metadata_json.get("release_date")
            doc_date = doc_metadata.get("release_date")
            
            if cutoff_date and doc_date:
                # If this doc represents a movie released after the cutoff, hide it
                if doc_date > cutoff_date:
                    return False
            
            # Also check chronological/release order index if available
            cutoff_order = cutoff_doc.metadata_json.get("timeline_position", {}).get("release_order")
            doc_order = doc_metadata.get("timeline_position", {}).get("release_order")
            if cutoff_order and doc_order and doc_order > cutoff_order:
                return False
                
            # If doc is a character profile, check if they were introduced after
            char_year = doc_metadata.get("chronological_year")
            cutoff_year = cutoff_doc.metadata_json.get("timeline_position", {}).get("chronological_order")
            # Simple chronological year comparison if available
            if char_year and cutoff_year and char_year > (2000 + cutoff_year):
                return False

    return True


def document_allowed(doc: Document, settings: Any, db: Session) -> bool:
    metadata = doc.metadata_json or {}
    return check_spoiler_filter(metadata, settings, db) and metadata_matches_filters(metadata, settings)

def search_knowledge_graph(query: str, db: Session) -> List[Dict[str, Any]]:
    """
    Searches the Entity Relationship knowledge graph for matches.
    E.g. "Who mentored Spider-Man?" -> finds 'mentored' relationship linked to 'peter_parker'.
    """
    results = []
    query_lower = query.lower()
    
    matched_entity_ids = [entity.id for entity in link_query_entities(query, db)]
            
    if not matched_entity_ids:
        return results

    relation_types = []
    for relation_type, keywords in RELATION_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            relation_types.append(relation_type)
        
    # Query relationships matching found entities
    for ent_id in matched_entity_ids:
        # Relationships where the entity is the source or target
        q_rels = db.query(Relationship).filter(
            (Relationship.source_entity_id == ent_id) | (Relationship.target_entity_id == ent_id)
        )
        
        # Filter by detected relationship types if any
        if relation_types:
            q_rels = q_rels.filter(Relationship.relation_type.in_(relation_types))
            
        for rel in q_rels.all():
            results.append({
                "type": "relationship",
                "source": rel.source_entity.name,
                "target": rel.target_entity.name,
                "relation": rel.relation_type,
                "description": rel.description
            })
            
    return results


def graph_results_to_retrieval_results(graph_results: List[Dict[str, Any]]) -> List[RetrievalResult]:
    results = []
    for graph in graph_results:
        title = f"{graph['source']} {graph['relation']} {graph['target']}"
        content = (
            f"Knowledge graph edge: {graph['source']} {graph['relation']} "
            f"{graph['target']}. {graph.get('description') or ''}"
        )
        results.append(
            RetrievalResult(
                document_id=f"graph:{graph['source']}:{graph['relation']}:{graph['target']}",
                title=title,
                category="graph",
                content=content,
                score=1.0,
                source_type="graph",
                metadata={
                    "source": graph["source"],
                    "target": graph["target"],
                    "relation": graph["relation"],
                    "reason": "Matched entity and relationship keywords in the question.",
                },
            )
        )
    return results

def search_documents_fts(query: str, settings: Any, db: Session) -> List[Document]:
    """
    Queries documents using SQLite FTS5 table with fallback to LIKE.
    """
    results = []
    
    # Strip any special FTS characters that might cause syntax errors
    clean_query = query.replace("'", "").replace('"', '').strip()
    if not clean_query:
        return []
        
    # Attempt FTS match
    fts_sql = text("""
        SELECT document_id FROM documents_fts 
        WHERE documents_fts MATCH :query 
        LIMIT 10
    """)
    
    try:
        # Try FTS search
        doc_ids = db.execute(fts_sql, {"query": f'"{clean_query}" OR {clean_query}'}).scalars().all()
        if doc_ids:
            results = db.query(Document).filter(Document.id.in_(doc_ids)).all()
    except Exception as e:
        print(f"FTS5 Query failed, falling back to LIKE: {e}")
        
    # Fallback to standard LIKE matching if no results or FTS errored
    if not results:
        like_query = f"%{clean_query}%"
        results = db.query(Document).filter(
            (Document.title.ilike(like_query)) | (Document.content.ilike(like_query))
        ).limit(5).all()

    # Apply spoiler filtering
    filtered_results = []
    for doc in results:
        if document_allowed(doc, settings, db):
            filtered_results.append(doc)
            
    return filtered_results

def hybrid_search_documents(query: str, settings: Any, db: Session, top_k: int = 5) -> List[Tuple[Document, float]]:
    """
    Performs hybrid search combining vector similarity (FAISS) and lexical keyword matching (FTS5).
    Applies spoiler preference filtering and ranks results.
    """
    from backend.app.retrieval.embeddings.faiss_manager import get_faiss_manager
    faiss_mgr = get_faiss_manager()
    
    # 1. Get FAISS vector search results (returns tuples of (Document, score))
    vector_results = faiss_mgr.search(query, top_k * 2, db)
    
    # 2. Get FTS keyword search results (returns list of Document)
    fts_results = search_documents_fts(query, settings, db)
    
    merged = {}  # doc_id -> (Document, score)
    
    # Add vector results (already spoiler filtered in search/check_spoiler)
    for doc, score in vector_results:
        # Re-verify spoiler filter just in case
        if document_allowed(doc, settings, db):
            merged[doc.id] = (doc, score)
            
    # Add/merge FTS results
    for doc in fts_results:
        if doc.id in merged:
            # Boost score if document matches both vector search and keyword match
            existing_doc, existing_score = merged[doc.id]
            merged[doc.id] = (existing_doc, min(existing_score + 0.25, 1.0))
        else:
            # Standard FTS match score fallback
            merged[doc.id] = (doc, 0.65)
            
    # Sort by score descending
    sorted_results = sorted(merged.values(), key=lambda x: x[1], reverse=True)
    return sorted_results[:top_k]


def search_exact_entity_documents(
    linked_entities: List[Entity],
    settings: Any,
    db: Session,
) -> List[Tuple[Document, float]]:
    results: List[Tuple[Document, float]] = []
    seen = set()
    for entity in linked_entities:
        candidates = db.query(Document).filter(Document.title.ilike(entity.name)).limit(5).all()
        if not candidates:
            candidates = db.query(Document).filter(Document.title.ilike(f"%{entity.name}%")).limit(5).all()
        for doc in candidates:
            if doc.id in seen or not document_allowed(doc, settings, db):
                continue
            seen.add(doc.id)
            results.append((doc, 0.95))
    return results


class HybridSearcher:
    """
    Production-facing retrieval orchestrator used by ChatService.
    It keeps the engine domain-agnostic while allowing the MCU graph data
    to contribute direct relationship evidence alongside document search.
    """

    def search(
        self,
        db: Session,
        query: str,
        settings: Any = None,
        top_k: int = 5,
    ) -> Tuple[List[RetrievalResult], str]:
        intent = detect_intent(query)
        expanded_queries = expand_query(query)
        merged: Dict[str, RetrievalResult] = {}
        linked_entities = link_query_entities(query, db)

        graph_results = search_knowledge_graph(query, db)
        for result in graph_results_to_retrieval_results(graph_results):
            merged[result.document_id] = result

        for doc, score in search_exact_entity_documents(linked_entities, settings, db):
            merged[doc.id] = RetrievalResult(
                document_id=doc.id,
                title=doc.title,
                category=doc.category,
                content=doc.content,
                score=score,
                source_type="entity_exact",
                metadata={
                    **(doc.metadata_json or {}),
                    "file_path": doc.file_path,
                    "linked_entities": [entity.id for entity in linked_entities],
                    "reason": "Boosted because the question directly named this entity or one of its aliases.",
                },
            )

        for expanded_query in expanded_queries:
            for doc, score in hybrid_search_documents(expanded_query, settings, db, top_k=top_k):
                existing = merged.get(doc.id)
                boosted_score = _entity_boosted_score(doc, score, linked_entities)
                result = RetrievalResult(
                    document_id=doc.id,
                    title=doc.title,
                    category=doc.category,
                    content=doc.content,
                    score=boosted_score,
                    source_type="hybrid",
                    metadata={
                        **(doc.metadata_json or {}),
                        "file_path": doc.file_path,
                        "query_variant": expanded_query,
                        "linked_entities": [entity.id for entity in linked_entities],
                        "reason": _retrieval_reason(doc, score, boosted_score),
                    },
                )
                if not existing or result.score > existing.score:
                    merged[doc.id] = result

        ranked = rerank_results(query, list(merged.values()))
        return ranked[:top_k], intent

    def build_context(self, results: List[RetrievalResult]) -> str:
        context_parts = []
        for result in results:
            reason = result.metadata.get("reason", "Retrieved as supporting context.")
            context_parts.append(
                f"[{result.title}] ({result.category}, {result.source_type}, score={result.score:.2f})\n"
                f"Reason: {reason}\n"
                f"{result.content[:900]}"
            )
        return "\n\n".join(context_parts)


def _entity_boosted_score(doc: Document, score: float, linked_entities: List[Entity]) -> float:
    title = doc.title.lower()
    content = doc.content.lower()
    for entity in linked_entities:
        names = [entity.name, *(entity.aliases_json or [])]
        if any(str(name).lower() == title for name in names):
            return min(score + 0.25, 1.0)
        if any(str(name).lower() in title or str(name).lower() in content[:500] for name in names):
            return min(score + 0.15, 1.0)
    return score


def _retrieval_reason(doc: Document, original_score: float, boosted_score: float) -> str:
    if boosted_score > original_score:
        return "Matched hybrid retrieval and received an entity-linking boost."
    return "Matched semantic vector search, keyword search, or both."
