# Phase 2.5: Knowledge Intelligence

Phase 2.5 deepens MCUVerse AI before Phase 3 infrastructure work. The focus is making the AI layer feel like the product: richer structured knowledge, graph reasoning, spoiler-aware retrieval, and explainable context assembly.

## Completed Scope

- Expanded the structured knowledge base from a small demo set to 22 ingested knowledge documents across movies, characters, artifacts, organizations, locations, timelines, watch orders, events, and relationships.
- Added representative MCU entities including Steve Rogers, Natasha Romanoff, Thor, Loki, Wanda Maximoff, Doctor Strange, the Avengers, TVA, Vormir, the Infinity Stones, the Tesseract, the Snap, and the Time Heist.
- Expanded coverage further with Guardians of the Galaxy, X-Men context, Deadpool, Wolverine, Eternals, Ms. Marvel, Agent Carter, Black Panther, Ant-Man, Moon Knight, Wakanda, Talokan, the Quantum Realm, and comic-origin bridge documents.
- Expanded relationship types and examples for `mentored`, `protege_of`, `member_of`, `enemy_of`, `ally_of`, `possesses`, `located_in`, `appears_in`, `introduced_in`, and `sibling_of`.
- Added a `HybridSearcher` orchestration class used by the service layer. It combines intent detection, query expansion, graph lookup, hybrid document search, reranking, and context assembly.
- Improved ingestion for generic YAML knowledge types so artifacts, organizations, locations, timelines, and events are indexed as readable source documents instead of raw dictionaries.
- Added regression coverage for graph-backed retrieval context.
- Fixed frontend build drift by restoring TypeScript path aliases, API client method compatibility, frontend type issues, and missing declared npm dependencies.

## Retrieval Flow

```text
User question
-> intent detection
-> query expansion
-> knowledge graph lookup
-> FAISS + keyword document search
-> spoiler filtering
-> result merge
-> reranking
-> context assembly with retrieval reasons
-> retrieval-only or configured LLM provider response
```

## Reviewer-Facing Queries

- "Who mentored Spider-Man?"
- "Who wielded the Infinity Stones?"
- "Show Tony Stark's relationships."
- "What happened between Infinity War and Endgame?"
- "Which characters appeared in Civil War?"
- "Tell me about the Time Heist."

## Verification

- Backend: `backend\.venv\Scripts\python.exe -m pytest backend\tests`
- Frontend: `npm.cmd run build`

Both checks passed after this phase.

## Remaining Phase 2.5 Opportunities

- Grow the dataset toward full MCU coverage with hundreds of entities and thousands of chunks.
- Add a formal knowledge validator for duplicate IDs, missing fields, broken relationships, and spoiler cutoff consistency.
- Add a visual graph explorer with React Flow or Cytoscape.
- Add a dedicated timeline API and richer timeline UI.
- Add evaluation benchmarks for retrieval accuracy, citation accuracy, latency, and confidence calibration.
