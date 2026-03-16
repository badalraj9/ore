# ORE: Open Research Engine

A deterministic, LLM-free system for large-scale scientific reasoning and intelligent data ingestion.

## Introduction

ORE (Open Research Engine) is an algorithmic pipeline designed to automate the synthesis of research papers from multiple academic sources. Unlike modern stochastic approaches that rely on Large Language Models (LLMs), ORE employs a deterministic pipeline combining classical Information Retrieval (IR), Graph Theory, and Statistical Analysis to ensure **reproducibility, traceability, and hallucination-free output**.

The system now includes a **generic smart data ingestion framework** that can be plugged into any system to automatically fetch, process, and index documents from multiple sources.

### Key Features

- **Deterministic Pipeline**: Every step is reproducible with fixed seeds
- **LLM-Free**: Uses TF-IDF, BM25, BERT embeddings for retrieval (not generation)
- **Multi-Source Ingestion**: Pluggable architecture supporting ArXiv, Semantic Scholar, PubMed, URLs, and files
- **Async Processing**: Background tasks with webhook notifications
- **Hybrid Retrieval**: Combines sparse (BM25) and dense (vector) search
- **Research Analysis**: Clustering, contradiction detection, citation graphs, gap identification
- **Production-Ready**: Error handling, validation, pagination, status tracking

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ORE Architecture                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────┐   │
│  │   Frontend   │    │                   Backend (FastAPI)              │   │
│  │   (React)    │    │                                                  │   │
│  └──────┬──────┘    │  ┌──────────────────────────────────────────┐  │   │
│         │           │  │              API Layer                      │  │   │
│         └──────────►│  │  /ingest  /search  /analyze  /process     │  │   │
│                     │  └────────────────────┬───────────────────────┘  │   │
│                     │                       │                           │   │
│                     │  ┌────────────────────▼───────────────────────┐  │   │
│                     │  │           Core Engine                       │  │   │
│                     │  │                                               │  │   │
│                     │  │  ┌─────────────┐ ┌──────────────────────┐ │  │   │
│                     │  │  │ Ingestion   │ │    Retrieval Engine   │ │  │   │
│                     │  │  │ Engine      │ │  ┌────────┐ ┌───────┐ │ │  │   │
│                     │  │  │             │ │  │ BM25   │ │ FAISS │ │ │  │   │
│                     │  │  │ ┌─────────┐ │ │  │(sparse)│ │(dense)│ │ │  │   │
│                     │  │  │ │Fetcher  │ │ │  └────────┘ └───────┘ │ │  │   │
│                     │  │  │ │Registry │ │ │       │         │       │ │  │   │
│                     │  │  │ └─────────┘ │ │       └────┬────┘       │ │  │   │
│                     │  │  └─────────────┘ │ │            ▼            │ │  │   │
│                     │  │                   │ │      RRF Fusion         │ │  │   │
│                     │  │  ┌─────────────┐ │ └──────────────────────┘ │  │   │
│                     │  │  │ Processing  │ │                            │  │   │
│                     │  │  │ Pipeline    │ │  ┌──────────────────────┐│  │   │
│                     │  │  │ ┌─────────┐ │ │  │    Analysis Engine     ││  │   │
│                     │  │  │ │Extractor │ │ │  │                        ││  │   │
│                     │  │  │ │Chunker  │ │ │  │ ┌──────┐ ┌──────────┐ ││  │   │
│                     │  │  │ │Canonical│ │ │  │ │Cluster│ │Contradict│ ││  │   │
│                     │  │  │ │Dedupe   │ │ │  │ │Engine │ │Detection │ ││  │   │
│                     │  │  │ └─────────┘ │ │  │ └──────┘ └──────────┘ ││  │   │
│                     │  │  └─────────────┘ │ │  │ ┌──────┐ ┌────────┐  ││  │   │
│                     │  │                   │ │  │ │Graph │ │Gap     │  ││  │   │
│                     │  │                   │ │  │ │Engine│ │Analysis│  ││  │   │
│                     │  │                   │ │  │ └──────┘ └────────┘  ││  │   │
│                     │  │                   │ │  └──────────────────────┘│  │   │
│                     │  │                   │ └──────────────────────────┘  │   │
│                     │  └───────────────────┼────────────────────────────┘   │
│                     │                       │                               │
│                     │  ┌────────────────────▼──────────────────────────┐   │
│                     │  │              Database Layer (SQLAlchemy)        │   │
│                     │  │                                                      │   │
│                     │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ │   │
│                     │  │  │ Papers │ │ Chunks │ │Entities│ │Tasks     │ │   │
│                     │  │  └────────┘ └────────┘ └────────┘ └──────────┘ │   │
│                     │  │                                                      │   │
│                     │  │  ┌────────────────────────────────────────────┐   │   │
│                     │  │  │           Vector Index (FAISS)              │   │   │
│                     │  │  └────────────────────────────────────────────┘   │   │
│                     │  └──────────────────────────────────────────────────┘   │
│                     └────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## System Phases

| Phase | Name | Description |
|-------|------|-------------|
| 0 | Bootstrapping | FastAPI + React + SQLite setup |
| 1 | Query Understanding | NLP pipeline for query parsing |
| 2 | Intelligent Ingestion | ArXiv Fetcher + Async download engine |
| 3 | Content Extraction | PDF → Structured JSON |
| 4 | Processing | Chunking, canonicalization, deduplication |
| 5 | Retrieval Engine | Hybrid BM25 + FAISS with RRF |
| 6 | Clustering | TF-IDF + K-Means topic grouping |
| 7 | Contradiction Detection | Polarity analysis |
| 8 | Citation Graph | NetworkX + Louvain community detection |
| 9 | Research Gap Identification | Method-Dataset matrix analysis |

## Workflow

### Ingestion Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Ingestion Workflow                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Client                                                                  │
│      │                                                                    │
│      ▼                                                                    │
│   POST /api/v1/ingest/start                                                │
│   {                                                                        │
│     "source": "arxiv",        ──────────────────────┐                    │
│     "query": "neural networks",                      │                    │
│     "max_results": 10,           Generic Ingest API  │                    │
│     "webhook_url": "https://..."                    │                    │
│   }                                             │                    │
│      │                                            ▼                    │
│      │                                    ┌───────────────┐               │
│      │                                    │ Task Created  │               │
│      │                                    │ task_id: uuid │               │
│      │                                    └───────┬───────┘               │
│      │                                            │                       │
│      │                                     Async Processing               │
│      │                                            │                       │
│      │                                            ▼                       │
│      │                                    ┌───────────────┐               │
│      │                                    │  Fetcher      │               │
│      │                                    │  Registry     │               │
│      │                                    └───────┬───────┘               │
│      │                                            │                       │
│      │                              ┌─────────────┼─────────────┐         │
│      │                              ▼             ▼             ▼        │
│      │                         ┌─────────┐  ┌───────────┐  ┌─────────┐    │
│      │                         │ ArXiv   │  │ Semantic  │  │  File   │    │
│      │                         │ Fetcher │  │ Scholar   │  │ Fetcher │    │
│      │                         └────┬────┘  └─────┬─────┘  └────┬────┘    │
│      │                              │             │             │         │
│      │                              └─────────────┼─────────────┘         │
│      │                                            ▼                       │
│      │                                   ┌───────────────┐                │
│      │                                   │ Download PDFs │                │
│      │                                   │ (concurrent) │                │
│      │                                   └───────┬───────┘                │
│      │                                           │                        │
│      │                                           ▼                        │
│      │                                   ┌───────────────┐                │
│      │                                   │ Extract Text │                │
│      │                                   │ Chunk Content│                │
│      │                                   └───────┬───────┘                │
│      │                                           │                        │
│      │                                           ▼                        │
│      │                                   ┌───────────────┐                │
│      │                                   │ Index (FAISS)│                │
│      │                                   │ Store (SQLite)                │
│      │                                   └───────┬───────┘                │
│      │                                           │                        │
│      │                                    ┌──────┴──────┐                 │
│      │                                    ▼             ▼                 │
│      │                           ┌───────────┐  ┌──────────┐             │
│      │                           │  Webhook  │  │ /status/ │             │
│      │                           │  Notifies │  │ task_id  │             │
│      │                           └───────────┘  └──────────┘             │
│      │                                                                    │
│      ▼                                                                    │
│   Response: {task_id: "uuid"}                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Search Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Search Workflow                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Client                                                                  │
│      │                                                                    │
│      ▼                                                                    │
│   POST /api/v1/search                                                     │
│   {                                                                        │
│     "query": "transformer attention",                                     │
│     "top_k": 10                                                           │
│   }                                                                        │
│      │                                                                    │
│      ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────┐         │
│   │              Retrieval Engine (Hybrid)                       │         │
│   │                                                              │         │
│   │    ┌─────────────────┐         ┌─────────────────┐         │         │
│   │    │  BM25 Search    │         │  FAISS Search    │         │         │
│   │    │  (Sparse)       │         │  (Dense)         │         │         │
│   │    │                 │         │                  │         │         │
│   │    │ • Tokenization  │         │ • BERT Embedding │         │         │
│   │    │ • Term Freq    │         │ • Cosine Sim     │         │         │
│   │    │ • IDF Weighting│         │ • KNN Search     │         │         │
│   │    └────────┬────────┘         └────────┬────────┘         │         │
│   │             │                           │                  │         │
│   │             └───────────┬───────────────┘                  │         │
│   │                         ▼                                  │         │
│   │                ┌─────────────────┐                         │         │
│   │                │  RRF Fusion     │                         │         │
│   │                │  (Rank Fusion)  │                         │         │
│   │                │                 │                         │         │
│   │                │ score = 1/(k+r) │                         │         │
│   │                │  where k=60      │                         │         │
│   │                └────────┬────────┘                         │         │
│   │                         │                                  │         │
│   │                         ▼                                  │         │
│   │                ┌─────────────────┐                         │         │
│   │                │  Re-rank       │                         │         │
│   │                │  Results       │                         │         │
│   │                └────────┬────────┘                         │         │
│   └─────────────────────────┼──────────────────────────────────┘         │
│                             │                                             │
│                             ▼                                             │
│                    ┌─────────────────┐                                     │
│                    │ Return Results │                                     │
│                    │ • chunk_id     │                                     │
│                    │ • score        │                                     │
│                    │ • text         │                                     │
│                    │ • paper_title  │                                     │
│                    │ • section      │                                     │
│                    └─────────────────┘                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ingest/start` | Start ingestion task |
| GET | `/api/v1/ingest/status/{task_id}` | Get task status |
| GET | `/api/v1/ingest/tasks` | List all tasks |
| GET | `/api/v1/ingest/sources` | List available sources |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/search` | Hybrid search |
| GET | `/api/v1/search?q=...` | Search via GET |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analyze/clusters` | Get topic clusters |
| GET | `/api/v1/analyze/graph` | Get citation graph |
| GET | `/api/v1/analyze/gaps` | Get research gaps |

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- SQLite (included)

### Backend Setup

```bash
# Navigate to backend
cd ore-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLP models
python -m spacy download en_core_web_sm
python -m nltk.downloader wordnet omw-1.4

# Run server
uvicorn main:app --reload
```

The backend will start at `http://localhost:8000`

API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

```bash
# Navigate to frontend
cd ore-frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will start at `http://localhost:5173`

## Configuration

All settings are in `ore-backend/config.py`:

```python
# Retrieval
DEFAULT_TOP_K: int = 10
RRF_K: int = 60
SPARSE_WEIGHT: float = 0.5
DENSE_WEIGHT: float = 0.5

# Chunking
CHUNK_SIZES: dict = {"abstract": 400, "introduction": 350, ...}
CHUNK_OVERLAPS: dict = {"abstract": 0, "introduction": 40, ...}

# Ingestion
MAX_INGEST_RETRIES: int = 3
MAX_CONCURRENT_DOWNLOADS: int = 5

# Security
CORS_ORIGINS: List[str] = ["http://localhost:5173"]
```

## Usage Examples

### Start Ingestion

```bash
curl -X POST http://localhost:8000/api/v1/ingest/start \
  -H "Content-Type: application/json" \
  -d '{
    "source": "arxiv",
    "query": "large language models",
    "max_results": 5,
    "webhook_url": "https://your-server.com/webhook"
  }'
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Ingestion task started"
}
```

### Check Status

```bash
curl http://localhost:8000/api/v1/ingest/status/550e8400-e29b-41d4-a716-446655440000
```

### Search

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "attention mechanism transformer",
    "top_k": 10
  }'
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Database | SQLite + SQLAlchemy |
| Vector Search | FAISS |
| Embeddings | SentenceTransformers (BERT) |
| NLP | spaCy, NLTK |
| ML | scikit-learn |
| Frontend | React + TypeScript |
| UI | TailwindCSS, Lucide Icons |

## License

MIT
