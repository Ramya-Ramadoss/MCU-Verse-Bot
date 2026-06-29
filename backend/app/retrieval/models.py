from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RetrievalResult:
    document_id: str
    title: str
    category: str
    content: str
    score: float
    source_type: str = "vector"
    metadata: dict = field(default_factory=dict)
