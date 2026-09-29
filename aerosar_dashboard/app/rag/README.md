# Standalone AEROSAR RAG Engine (Step 18)

This module implements a standalone Retrieval-Augmented Generation (RAG) engine for the STALLION AEROSAR project. 
It enables the system to retrieve relevant operational guidelines, safety protocols, and incident context from a local knowledge base, based on structured incidents.

## What it does
- Loads documents (Markdown/JSON) from a `knowledge_base` directory.
- Chunks documents into smaller retrieval units.
- Embeds text using a pure-Python TF-IDF word frequency implementation (zero heavy dependencies for the first iteration).
- Stores vectors in a local, in-memory dictionary store.
- Maps an `Incident` to a search query using `QueryBuilder`.
- Retrieves the top-K relevant chunks via `Retriever`.
- Wraps this functionality into `RAGService`.

## What it does NOT do
- It does **NOT** call an LLM. (That is for Step 19).
- It does **NOT** integrate with the FastAPI routes or Dashboard yet.
- It does **NOT** process raw video, ROS topics, or MAVLink telemetry.

## Architecture

```
Incident ─────────→ QueryBuilder
                         │
Knowledge Base ───→ Vector Store (Chunker + Embeddings)
                         │
                         ↓
                     Retriever
                         │
                         ↓
                     RAGResult
```

## How to test
You can run the interactive CLI test which uses mock incidents:
```bash
python -m app.rag.cli
```

You can also run the pytest suite:
```bash
pytest tests/test_step18_rag.py -v
```

## How to add documents
Place `.md` or `.json` files inside subdirectories of `knowledge_base/` (e.g., `knowledge_base/rescue/`).
The system will automatically load, chunk, and index them when `RAGService.index_knowledge_base()` is called.
