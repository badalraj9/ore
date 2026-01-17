# ORE: Open Research Engine

ORE is an algorithmic, LLM-free system for large-scale scientific reasoning.

## Phases Implemented
- **Phase 0**: System Bootstrapping (FastAPI + React + SQLite).
- **Phase 1**: Intelligent Query Understanding (NLP pipeline).
- **Phase 2**: Intelligent Ingestion (ArXiv Fetcher + Async Engine).
- **Phase 3**: Content Extraction (PDF -> Structured JSON).
- **Phase 4**: Processing (Chunking, Canonicalization, Deduplication).
- **Phase 5**: Retrieval Engine (Hybrid Sparse + Dense).
- **Phase 6**: Clustering (TF-IDF + K-Means).
- **Phase 7**: Contradiction Detection (Polarity Analysis).
- **Phase 8**: Citation Graph (NetworkX + Louvain).
- **Phase 9**: Research Gap Identification (Method-Dataset Matrix).

## Robustness Features
- **Retry Logic**: ArXiv fetcher retries 3 times with exponential backoff.
- **Concurrency**: Asyncio-based ingestion with SQLite locking for thread safety.
- **NLP Handling**: Slang mapping ("stuff" -> "methods"), noise removal ("idk"), and intent classification.

## Setup

### Backend
1. Navigate to `ore-backend/`:
   ```bash
   cd ore-backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Download NLP models:
   ```bash
   python -m spacy download en_core_web_sm
   python -m nltk.downloader wordnet omw-1.4
   ```
4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend
1. Navigate to `ore-frontend/`:
   ```bash
   cd ore-frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the dev server:
   ```bash
   npm run dev
   ```

## Testing
Run the comprehensive stress test suite to verify robustness:
```bash
python scripts/stress_test.py
```
4. **Test Processing (Phase 4)**:
   ```bash
   python scripts/test_phase4.py
   ```
5. **Test Phases 5-7**:
   ```bash
   python scripts/test_phases_5_7.py
   ```
6. **Test Phases 8-9 (Final)**:
   ```bash
   python scripts/stress_test_final.py
   ```
This runs 10 scenarios including network failure simulation, concurrent load, and edge-case query parsing.
