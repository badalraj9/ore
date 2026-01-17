# Database & Data Schema

ORE uses SQLite for its simplicity and reliability in local-first deployments. The schema is normalized to separate document metadata from content chunks and derived knowledge entities.

## ER Diagram (Conceptual)

```
[Paper] 1 --- * [Chunk]
               |
               *
            [Entity] (Logical link via text matching)
```

## Schema Definitions

### 1. `papers` Table
Stores high-level metadata about an academic paper.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-incrementing ID. |
| `title` | String | Normalized title. Indexed. |
| `authors` | String | JSON string or CSV of author names. |
| `abstract` | Text | Full abstract text. |
| `doi` | String | Digital Object Identifier. Unique constraint. |
| `ingested_at` | DateTime | Timestamp of ingestion. |
| `filepath_processed`| String | Path to the CLEAN text file on disk. |

### 2. `chunks` Table
Stores the atomic units of text used for retrieval and analysis.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-incrementing ID. |
| `paper_id` | Integer (FK) | Foreign Key to `papers`. |
| `section` | String | The section header (e.g., "Results"). |
| `text` | Text | The actual content of the chunk. |
| `token_count` | Integer | Length of the chunk (for filtering). |
| `embedding_id` | String | (Optional) Ref ID for external vector stores. |

### 3. `entities` Table
Stores canonical concepts derived or extracted from the text.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-incrementing ID. |
| `canonical_name` | String | The normalized name (e.g., "Transformer"). |
| `aliases` | Text | JSON list of synonyms (e.g., `["Self-Attention", "Transformers"]`). |
| `category` | String | The inferred type: `Method`, `Dataset`, `Metric`. |

## Persistence Strategy

*   **Metadata:** All structured data is ACID-compliant via SQLite.
*   **Vector Index:** The FAISS index is *not* stored in SQLite. It is serialized to a binary file (`faiss_index.bin`) alongside a pickle file (`chunk_ids.pkl`) that maps matrix rows back to Database IDs.
    *   *Risk:* The DB and Vector Index can get out of sync if the DB is modified without rebuilding the index. The `DenseRetriever` handles this by supporting a `force_rebuild` flag.
