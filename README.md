<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=250&color=0:8A2BE2,100:FF1493&text=MCUVerse%20AI%20ChatBot&fontSize=55&fontColor=ffffff&animation=fadeIn&fontAlignY=40" />
</p>

---

# MCUVerse AI ChatBot

Enterprise-grade AI knowledge assistant for the Marvel Cinematic Universe and complete comics details. Built with a domain-agnostic retrieval engine and a swappable MCU knowledge layer.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green)
![React](https://img.shields.io/badge/React-18-61DAFB)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Quick Start

### Backend

```bash
cd "MCUVerse Chat bot"
python -m venv backend/.venv
backend\.venv\Scripts\activate   # Windows
pip install -r backend/requirements.txt
set PYTHONPATH=.
uvicorn backend.app.main:app --reload --port 8000
```

On first startup, the API auto-ingests `knowledge/` and builds the FAISS index.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## Features

- **Hybrid Retrieval** — FAISS vector search + SQLite FTS5 keyword search + knowledge graph
- **Graph Reasoning** — Entity relationship lookups for mentors, allies, wielders, appearances, locations, and team membership
- **Knowledge Intelligence** — Intent detection, query expansion, reranking, and explainable context assembly
- **Expanded MCU + Comics Base** — 80 local knowledge documents across MCU films, Disney+ series, teams, artifacts, X-Men/Deadpool context, and comic-origin notes
- **Spoiler Protection** — Spoiler-free, partial, or full knowledge modes
- **JWT Auth + Guest Mode** — Register, login, guest sessions, and user-scoped chat history
- **Admin Control Center** — Analytics, document inspection, knowledge ingestion, and FAISS reindexing
- **LLM Abstraction** — Gemini, OpenAI, Ollama, or retrieval-only (no API key required)
- **Optional Cache** — Memory (dev), SQLite, or Redis (production)
- **Premium UI** — J.A.R.V.I.S.-inspired glassmorphism chat interface
- **Analytics** — Retrieval latency, confidence, embedding counts



### Docker

```bash
docker compose up --build
```

- API: http://localhost:8000
- UI: http://localhost:3000

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/guest` | Create guest session |
| GET | `/api/v1/auth/me` | Current user |
| POST | `/api/v1/chat/conversations` | Create conversation |
| POST | `/api/v1/chat/conversations/{id}/messages` | Send message |
| GET | `/api/v1/knowledge/documents` | List documents |
| POST | `/api/v1/knowledge/reindex` | Rebuild embeddings |
| GET | `/api/v1/analytics` | System analytics |

Full docs: http://localhost:8000/api/v1/docs

## Configuration

Copy `.env.example` to `.env` and set:

```env
LLM_PROVIDER=retrieval_only   # or gemini, openai, ollama
GEMINI_API_KEY=your-key
CACHE_PROVIDER=memory
```

## Architecture

```
User Question → Query Cleaning → Intent Detection → Hybrid Search
    → Spoiler Filter → Re-ranking → LLM (optional) → Response + Citations
```

Frontend routes:

- `/` — chat workspace
- `/login` — login, register, guest mode
- `/dashboard` — analytics and admin operations

See `docs/` for phase reports and architecture details, including `docs/PHASE2_5_KNOWLEDGE_INTELLIGENCE.md`, `docs/PHASE3.md`, and `docs/BUILD_REPORT.md`.

## Project Structure

```
backend/          FastAPI app, retrieval engine, services
frontend/         React + TypeScript + Tailwind UI
knowledge/        MCU YAML knowledge base (swappable)
embeddings/       FAISS index storage
docs/             Phase documentation
.github/          CI workflow
```

## Tests

```bash
set PYTHONPATH=.
backend\.venv\Scripts\python.exe -m pytest backend/tests -q
```

## License

MIT
