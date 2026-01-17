# Module Implementation Guide

This document serves as a developer's guide to the `ore-backend` codebase.

## Directory Structure

```
ore-backend/
├── core/
│   ├── ingestion/       # PDF parsing, cleaning, chunking
│   ├── processing/      # Background tasks, queue management (conceptually)
│   ├── retrieval/       # Search engines (Sparse/Dense)
│   ├── analysis/        # Clustering, Gap Analysis, Graphs
│   └── query_engine.py  # Orchestrator
├── database.py          # SQLAlchemy models and connection
├── main.py              # FastAPI entry point
└── config.py            # Configuration loader
```

## Key Modules

### 1. Ingestion (`core/ingestion`)
*   **Purpose:** Converts raw content into structured database rows.
*   **Key Classes:**
    *   `fetchers.py` / `ArxivFetcher`:
        *   Interacts with the ArXiv API to search for papers.
        *   Implements async PDF downloading with **exponential backoff** retry logic to handle network instability.
    *   `Normalizer`: Static class for text cleaning (NFKC, regex).
    *   `Chunker`: Splits text into sliding windows or by section.

### 2. Retrieval (`core/retrieval`)
*   **`bm25.py` / `SparseRetriever`**:
    *   Maintains an in-memory `BM25Okapi` object.
    *   *Note:* Rebuilds index on first search if not initialized.
*   **`vector.py` / `DenseRetriever`**:
    *   Manages the FAISS index.
    *   Handles disk persistence (`faiss_index.bin`) to avoid re-embedding on restart.

### 3. Analysis (`core/analysis`)
*   **`gaps.py` / `GapIdentifier`**:
    *   Contains the logic for the Method-Dataset matrix.
    *   Relies on `Entity` table in DB.
*   **`clustering.py` / `ClusterEngine`**:
    *   Wraps `sklearn`.
    *   Exposes `cluster_chunks(paper_id)` method.

### 4. Database (`database.py`)
*   Uses a single file `sqlite.db` (by default).
*   `SessionLocal` is a factory for database sessions.
*   **Best Practice:** Always close sessions in a `finally` block or use context managers to prevent connection leaks (SQLite lock errors).

## Common Workflows

### Adding a New Algorithm
1.  Create a new file in `core/analysis`.
2.  Define a class that accepts `Session` or raw data.
3.  Implement a deterministic `run()` method.
4.  Import and expose it in the Gradio UI or API.

### Modifying the Schema
1.  Edit `database.py` to add columns/tables.
2.  Since no automatic migration tool (like Alembic) is configured in the minimal setup, you must manually alter the SQLite file or delete it to regenerate (for dev).
