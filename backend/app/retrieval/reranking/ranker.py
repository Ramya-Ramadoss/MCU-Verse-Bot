import re
from typing import List

from backend.app.retrieval.models import RetrievalResult


def rerank_results(query: str, results: List[RetrievalResult]) -> List[RetrievalResult]:
    q_tokens = set(re.findall(r"\w+", query.lower()))
    scored = []
    for r in results:
        text = f"{r.title} {r.content}".lower()
        lexical = sum(1 for t in q_tokens if t in text) / max(len(q_tokens), 1)
        type_boost = {"graph": 0.15, "vector": 0.05, "keyword": 0.08}.get(r.source_type, 0)
        final = r.score * 0.7 + lexical * 0.25 + type_boost
        scored.append((final, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]
