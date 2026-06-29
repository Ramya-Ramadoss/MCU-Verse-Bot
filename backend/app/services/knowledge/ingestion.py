import os
import yaml
import json
from sqlalchemy.orm import Session
from backend.app.db.models.document import Document
from backend.app.db.models.graph import Entity, Relationship

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
    title = data.get("title", data.get("name", data.get("id", "Untitled")))
    summary = data.get("summary", data.get("description", data.get("content", "")))
    details = []
    for key, value in data.items():
        if key in {"id", "title", "name", "type", "summary", "description", "content"}:
            continue
        if isinstance(value, list):
            details.append(f"{key.replace('_', ' ').title()}: {', '.join(str(item) for item in value)}")
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

    # Step 1: Process character profiles and movie profiles
    for root, _, files in os.walk(knowledge_dir):
        category = os.path.basename(root)
        if category in ["relationships", "knowledge"]:
            # Skip relationships for the second pass
            continue
            
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
                continue

            entity_id = data["id"]
            entity_type = data.get("type", "unknown")
            
            # Determine content and metadata based on type
            content = ""
            metadata = {}
            name = ""
            
            if entity_type == "character":
                content = construct_character_content(data)
                name = data.get("name", entity_id)
                metadata = {
                    "spoiler_level": data.get("spoiler_level", "none"),
                    "aliases": data.get("aliases", []),
                    "status": data.get("status", "unknown"),
                    "release_order_index": data.get("release_order_index", 0),
                    "chronological_year": data.get("chronological_year")
                }
            elif entity_type == "movie":
                content = construct_movie_content(data)
                name = data.get("title", entity_id)
                metadata = {
                    "spoiler_level": data.get("spoiler_level", "none"),
                    "phase": data.get("phase"),
                    "release_date": data.get("release_date"),
                    "timeline_position": data.get("timeline_position", {})
                }
            else:
                name = data.get("title", data.get("name", entity_id))
                content = construct_generic_content(data)
                metadata = {
                    **data.get("metadata", {}),
                    "spoiler_level": data.get("spoiler_level", "none"),
                    "release_date": data.get("release_date"),
                    "timeline_position": data.get("timeline_position", {}),
                    "release_order_index": data.get("release_order_index", 0),
                    "chronological_year": data.get("chronological_year"),
                }
            
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
            entity.description = data.get(
                "biography",
                data.get("synopsis", data.get("summary", data.get("description", ""))),
            )
            
            stats["documents"] += 1
            stats["entities"] += 1

    db.commit()

    # Step 2: Process relationships.yaml
    rel_path = os.path.join(knowledge_dir, "relationships", "relationships.yaml")
    if os.path.exists(rel_path):
        with open(rel_path, "r", encoding="utf-8") as f:
            try:
                rel_data = yaml.safe_load(f)
            except Exception as e:
                print(f"Error parsing relationships YAML: {e}")
                rel_data = {}
                
        if rel_data and "relationships" in rel_data:
            # Delete old relationships to avoid duplicates/stale links
            db.query(Relationship).delete()
            
            pending_stub_ids = set()
            for item in rel_data["relationships"]:
                source_id = item.get("source_id")
                target_id = item.get("target_id")
                rel_type = item.get("relation_type")
                desc = item.get("description")
                
                if not source_id or not target_id or not rel_type:
                    continue
                
                # Check that source and target exist as entities. If not, create stub entities
                for ent_id in [source_id, target_id]:
                    if ent_id in pending_stub_ids:
                        continue
                    ent = db.query(Entity).filter(Entity.id == ent_id).first()
                    if not ent:
                        # Stub entity placeholder
                        ent = Entity(
                            id=ent_id,
                            name=ent_id.replace("_", " ").title(),
                            type="character" if "team" not in ent_id else "team",
                            description="Stub entity created during relationship ingestion."
                        )
                        db.add(ent)
                        pending_stub_ids.add(ent_id)
                        stats["entities"] += 1
                
                # Add relationship
                relationship_obj = Relationship(
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    relation_type=rel_type,
                    description=desc
                )
                db.add(relationship_obj)
                stats["relationships"] += 1
                
            db.commit()
            
    print(f"Ingestion completed. Stats: {stats}")
    return stats
