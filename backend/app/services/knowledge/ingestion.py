import os
import yaml
import json
from sqlalchemy.orm import Session
from backend.app.db.models.document import Document
from backend.app.db.models.graph import Entity, Relationship
from backend.app.services.knowledge.schema import (
    RelationshipSpec,
    canonical_description,
    canonical_metadata,
    canonical_title,
    extract_relationship_specs,
    normalize_knowledge_type,
    relationship_specs_from_root,
)

def construct_character_content(data: dict) -> str:
    aliases = ", ".join(data.get("aliases", []))
    powers = ", ".join(data.get("powers", []))
    weaknesses = ", ".join(data.get("weaknesses", []))
    weapons = ", ".join(data.get("weapons", []))
    affiliations = ", ".join(data.get("affiliations", []))
    
    return f"""Character Name: {data.get('name')}
Aliases: {aliases}
Type: Character
Status: {data.get('status')}
Biography: {data.get('biography')}
Powers: {powers}
Weaknesses: {weaknesses}
Weapons: {weapons}
Affiliations: {affiliations}
"""

def construct_movie_content(data: dict) -> str:
    events = "\n".join([f"- {event}" for event in data.get("major_events", [])])
    introduced = ", ".join(data.get("characters_introduced", []))
    
    return f"""Movie Title: {data.get('title')}
Type: Movie
Phase: {data.get('phase')}
Release Date: {data.get('release_date')}
Runtime: {data.get('runtime_minutes')} minutes
Director: {data.get('director')}
Main Villain: {data.get('main_villain')}
Synopsis: {data.get('synopsis')}
Major Events:
{events}
Characters Introduced: {introduced}
Post-Credit Scene: {data.get('post_credit_scene')}
"""

def construct_generic_content(data: dict) -> str:
    title = canonical_title(data)
    summary = data.get("summary", data.get("description", data.get("content", "")))
    details = []
    for key, value in data.items():
        if key in {"id", "title", "name", "type", "summary", "description", "content", "relationships"}:
            continue
        if isinstance(value, list):
            details.append(f"{key.replace('_', ' ').title()}: {_format_list_value(value)}")
        elif isinstance(value, dict):
            details.append(f"{key.replace('_', ' ').title()}: {json.dumps(value)}")
        else:
            details.append(f"{key.replace('_', ' ').title()}: {value}")

    detail_text = "\n".join(details)
    return f"""Name: {title}
Type: {data.get('type', 'knowledge')}
Summary: {summary}
{detail_text}
"""


def _format_list_value(value: list) -> str:
    rendered = []
    for item in value:
        if isinstance(item, dict):
            rendered.append(json.dumps(item))
        else:
            rendered.append(str(item))
    return ", ".join(rendered)


def _upsert_stub_entity(
    db: Session,
    entity_id: str,
    relation_type: str = "",
    known_entity_ids: set[str] | None = None,
) -> bool:
    if known_entity_ids is not None and entity_id in known_entity_ids:
        return False

    existing = db.query(Entity).filter(Entity.id == entity_id).first()
    if existing:
        if known_entity_ids is not None:
            known_entity_ids.add(entity_id)
        return False

    inferred_type = "team" if "team" in entity_id or relation_type in {"member_of", "has_member"} else "unknown"
    db.add(
        Entity(
            id=entity_id,
            name=entity_id.replace("_", " ").title(),
            type=inferred_type,
            description="Stub entity created during relationship ingestion.",
        )
    )
    if known_entity_ids is not None:
        known_entity_ids.add(entity_id)
    return True


def _insert_relationships(db: Session, relationship_specs: list[RelationshipSpec]) -> int:
    db.query(Relationship).delete()
    known_entity_ids = {entity_id for (entity_id,) in db.query(Entity.id).all()}
    inserted = 0
    for spec in relationship_specs:
        _upsert_stub_entity(db, spec.source_id, spec.relation_type, known_entity_ids)
        _upsert_stub_entity(db, spec.target_id, spec.relation_type, known_entity_ids)
        db.add(
            Relationship(
                source_entity_id=spec.source_id,
                target_entity_id=spec.target_id,
                relation_type=spec.relation_type,
                description=spec.description,
            )
        )
        inserted += 1
    return inserted


def ingest_all_knowledge(db: Session, knowledge_dir: str):
    """
    Scans the knowledge directory and ingests movies, characters, series,
    and relationships into the database.
    """
    print(f"Starting knowledge ingestion from {knowledge_dir}...")
    
    # Track files processed
    stats = {
        "documents": 0,
        "entities": 0,
        "relationships": 0
    }

    relationship_specs: list[RelationshipSpec] = []

    # Step 1: Process modular knowledge profiles
    for root, _, files in os.walk(knowledge_dir):
        category = os.path.basename(root)
            
        for file in files:
            if not (file.endswith(".yaml") or file.endswith(".yml")):
                continue
                
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = yaml.safe_load(f)
                except Exception as e:
                    print(f"Error parsing YAML file {file_path}: {e}")
                    continue
            
            if not data or "id" not in data:
                if category == "relationships" and data:
                    relationship_specs.extend(relationship_specs_from_root(data))
                continue

            entity_id = data["id"]
            entity_type = normalize_knowledge_type(data.get("type"), category)
            
            # Determine content and metadata based on type
            content = ""
            metadata = {}
            name = ""
            
            if entity_type == "character":
                content = construct_character_content(data)
                name = data.get("name", entity_id)
                metadata = {
                    **canonical_metadata(data, category),
                    "aliases": data.get("aliases", []),
                    "status": data.get("status", "unknown"),
                }
            elif entity_type == "movie":
                content = construct_movie_content(data)
                name = data.get("title", entity_id)
                metadata = {
                    **canonical_metadata(data, category),
                    "phase": data.get("phase"),
                }
            else:
                name = canonical_title(data)
                content = construct_generic_content(data)
                metadata = canonical_metadata(data, category)
            
            # 1. Upsert into Document
            doc = db.query(Document).filter(Document.file_path == file_path).first()
            if not doc:
                doc = Document(file_path=file_path)
                db.add(doc)
            
            doc.title = name
            doc.category = category
            doc.content = content
            doc.metadata_json = metadata
            
            # 2. Upsert into Entity
            entity = db.query(Entity).filter(Entity.id == entity_id).first()
            if not entity:
                entity = Entity(id=entity_id)
                db.add(entity)
            
            entity.name = name
            entity.type = entity_type
            entity.aliases_json = data.get("aliases", [])
            entity.description = canonical_description(data)
            relationship_specs.extend(extract_relationship_specs(data))
            
            stats["documents"] += 1
            stats["entities"] += 1

    db.commit()

    # Step 2: Materialize all explicit and derived graph edges in one pass.
    if relationship_specs:
        before_entities = db.query(Entity).count()
        stats["relationships"] = _insert_relationships(db, relationship_specs)
        db.commit()
        stats["entities"] += max(db.query(Entity).count() - before_entities, 0)
            
    print(f"Ingestion completed. Stats: {stats}")
    return stats
