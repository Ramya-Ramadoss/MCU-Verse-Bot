# Phase 2 — Embeddings, Retrieval Engine & Frontend

**Status: Complete**

## Deliverables

### Embedding Pipeline
- `EmbeddingService` — SentenceTransformers (`all-MiniLM-L6-v2`)
- FAISS `IndexFlatIP` with normalized vectors
- Chunk tracking in `EmbeddingTrack` table
- Auto-build on startup if index missing

### Hybrid Retrieval Pipeline
```
Query Cleaning → Intent Detection → Query Expansion
  → Vector (FAISS) + Keyword (FTS5) + Graph (Relationships)
  → Merge → Re-rank → Spoiler Filter → Top-K Context
```

- **Intent types:** general, relationship, timeline, entity
- **Re-ranking:** Lexical overlap + source-type boost
- **Spoiler filtering:** Respects user spoiler preference settings

### LLM Provider Abstraction
- `BaseLLMProvider` interface
- Implementations: `RetrievalOnlyProvider`, `GeminiProvider`, `OpenAIProvider`, `OllamaProvider`
- Auto-fallback to retrieval-only when no API key configured

### Cache Service
- Adapters: Memory (default), SQLite, Redis (optional)
- Query response caching with SHA256 keys

### Chat API
- `POST /api/v1/chat/conversations` — Create conversation
- `POST /api/v1/chat/conversations/{id}/messages` — Send message, get cited response
- `GET /api/v1/analytics` — System metrics

### Frontend (React + TypeScript + Tailwind)
- J.A.R.V.I.S.-inspired glassmorphism UI
- Chat with markdown rendering, citations, confidence scores
- Settings panel (LLM provider, spoiler mode, top-k)
- Suggested questions, conversation sidebar
- Framer Motion animations

## Verification

```bash
# Backend tests
PYTHONPATH=. pytest backend/tests -q

# Start backend + frontend
uvicorn backend.app.main:app --reload
cd frontend && npm run dev
```

Try: *"Who mentored Spider-Man?"* — should return graph + retrieval results with Tony Stark citation.

## Next Phase

Phase 3: JWT auth, OAuth, admin dashboard, Docker production config, CI/CD.
