# RAG (v0.5)

## Components
- `rag/embedder.py`: OpenAI embeddings with sparse token fallback.
- `rag/vector_store.py`: JSON-backed store (`data/rag_index.json`) that supports dense cosine or sparse jaccard.
- `rag/retriever.py`: indexing helpers and retrieval of top-k chunks.

## Indexed sources
- Notes (`data/notes/*.txt` full text).
- Static facts (`memory.json:facts`).
- Dynamic facts (`memory.json:dynamic_facts` captured at runtime).
- Plans (`data/planner.json` via planner skill and orchestrator).
- Vision-ingested text (screen summaries, camera snapshots, PDFs ingested).
- Journal entries (text + mood-tagged) when retriever is available.

## Flow
1. Startup bootstraps notes + memory into the vector store.
2. New dynamic facts and plans are indexed on creation.
3. On each user query, orchestrator retrieves top_k chunks and injects them as system context before LLM.

## Configuration
- Uses `OPENAI_API_KEY` for embeddings when available; otherwise sparse fallback.
- Store location: `data/rag_index.json`.

## Extensibility
- Swap vector_store implementation for FAISS/SQLite without changing retriever API.
- Add chunking over longer documents; current setup uses whole-note granularity.
