from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Iterable, List, Optional


SUPPORTED_KNOWLEDGE_TYPES = {
    "artifact",
    "character",
    "comic_event",
    "comics",
    "cosmic_entity",
    "event",
    "location",
    "movie",
    "multiverse_earth",
    "organization",
    "quote",
    "series",
    "species",
    "team",
    "timeline",
    "variant",
    "vehicle",
    "watch_order",
    "weapon",
}

RELATION_FIELD_MAP = {
    "affiliations": "member_of",
    "allies": "ally_of",
    "appears_in": "appears_in",
    "children": "parent_of",
    "created": "created",
    "created_by": "created_by",
    "creators": "created_by",
    "enemies": "enemy_of",
    "family": "related_to",
    "members": "has_member",
    "parents": "child_of",
    "possesses": "possesses",
    "siblings": "sibling_of",
    "variants": "has_variant",
    "variant_of": "variant_of",
    "wields": "possesses",
}

COLLECTION_FIELDS = {
    "abilities",
    "aliases",
    "appearances",
    "artifacts",
    "continuities",
    "creators",
    "earths",
    "events",
    "key_issues",
    "locations",
    "objects",
    "organizations",
    "power_sets",
    "quotes",
    "relationships",
    "species",
    "teams",
    "timeline_events",
    "variants",
    "weapons",
}


@dataclass(frozen=True)
class RelationshipSpec:
    source_id: str
    target_id: str
    relation_type: str
    description: str = ""


def normalize_knowledge_type(raw_type: Optional[str], category: str) -> str:
    value = (raw_type or category or "knowledge").strip().lower().replace("-", "_")
    if value.endswith("s") and value[:-1] in SUPPORTED_KNOWLEDGE_TYPES:
        value = value[:-1]
    return value if value in SUPPORTED_KNOWLEDGE_TYPES else value


def canonical_title(data: Dict[str, Any]) -> str:
    return data.get("title") or data.get("name") or data.get("id") or "Untitled"


def normalize_entity_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return normalized.strip("_")


def canonical_description(data: Dict[str, Any]) -> str:
    for key in ("biography", "synopsis", "summary", "description", "content"):
        value = data.get(key)
        if value:
            return str(value)
    return ""


def canonical_metadata(data: Dict[str, Any], category: str) -> Dict[str, Any]:
    embedded = data.get("metadata") or {}
    metadata = {
        **embedded,
        "knowledge_type": normalize_knowledge_type(data.get("type"), category),
        "continuity": data.get("continuity", embedded.get("continuity", "unspecified")),
        "canon_status": data.get("canon_status", embedded.get("canon_status", "unspecified")),
        "source_status": data.get("source_status", embedded.get("source_status", "local_curated")),
        "universe": data.get("universe", embedded.get("universe")),
        "earth": data.get("earth", embedded.get("earth")),
        "spoiler_level": data.get("spoiler_level", embedded.get("spoiler_level", "none")),
        "release_date": data.get("release_date", embedded.get("release_date")),
        "timeline_position": data.get("timeline_position", embedded.get("timeline_position", {})),
        "release_order_index": data.get("release_order_index", embedded.get("release_order_index", 0)),
        "chronological_year": data.get("chronological_year", embedded.get("chronological_year")),
    }

    for field in COLLECTION_FIELDS:
        if field in data:
            metadata[field] = data[field]

    return {key: value for key, value in metadata.items() if value not in (None, "", [])}


def extract_relationship_specs(data: Dict[str, Any]) -> List[RelationshipSpec]:
    source_id = data.get("id")
    if not source_id:
        return []

    specs: List[RelationshipSpec] = []
    for item in data.get("relationships", []) or []:
        if not isinstance(item, dict):
            continue
        spec = _relationship_from_mapping(item, default_source_id=source_id)
        if spec:
            specs.append(spec)

    for field, relation_type in RELATION_FIELD_MAP.items():
        if field not in data:
            continue
        for target_id in _iter_target_ids(data[field], normalize_strings=True):
            specs.append(
                RelationshipSpec(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type,
                    description=f"Derived from {field} on {canonical_title(data)}.",
                )
            )

    return _dedupe_relationships(specs)


def relationship_specs_from_root(data: Dict[str, Any]) -> List[RelationshipSpec]:
    specs: List[RelationshipSpec] = []
    for item in data.get("relationships", []) or []:
        if not isinstance(item, dict):
            continue
        spec = _relationship_from_mapping(item)
        if spec:
            specs.append(spec)
    return _dedupe_relationships(specs)


def _relationship_from_mapping(
    item: Dict[str, Any],
    default_source_id: Optional[str] = None,
) -> Optional[RelationshipSpec]:
    source_id = item.get("source_id") or item.get("source") or default_source_id
    target_id = item.get("target_id") or item.get("target")
    relation_type = item.get("relation_type") or item.get("relationship") or item.get("type")
    if not source_id or not target_id or not relation_type:
        return None
    return RelationshipSpec(
        source_id=str(source_id),
        target_id=str(target_id),
        relation_type=str(relation_type),
        description=str(item.get("description") or ""),
    )


def _iter_target_ids(value: Any, normalize_strings: bool = False) -> Iterable[str]:
    if isinstance(value, str):
        yield normalize_entity_id(value) if normalize_strings else value
        return
    if isinstance(value, dict):
        target_id = value.get("id") or value.get("target_id") or value.get("target")
        if target_id:
            target = str(target_id)
            yield normalize_entity_id(target) if normalize_strings else target
        return
    if isinstance(value, list):
        for item in value:
            yield from _iter_target_ids(item, normalize_strings=normalize_strings)


def _dedupe_relationships(specs: List[RelationshipSpec]) -> List[RelationshipSpec]:
    seen = set()
    deduped = []
    for spec in specs:
        key = (spec.source_id, spec.target_id, spec.relation_type, spec.description)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(spec)
    return deduped
