from typing import List, Dict, Any
from core.retrieval.bm25 import SparseRetriever
from core.retrieval.vector import DenseRetriever
from database import SessionLocal, Chunk, Paper

class RetrievalEngine:
    def __init__(self):
        self.sparse = SparseRetriever()
        self.dense = DenseRetriever()

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Hybrid Search: Combines BM25 and Dense scores using Reciprocal Rank Fusion (RRF)
        or simple weighted sum (if normalized).
        Here we use RRF for simplicity (no need to normalize distribution).
        """
        sparse_res = self.sparse.search(query, top_k=top_k*2)
        dense_res = self.dense.search(query, top_k=top_k*2)

        # RRF
        k = 60
        scores = {}

        for rank, (cid, _) in enumerate(sparse_res):
            scores[cid] = scores.get(cid, 0) + (1 / (k + rank + 1))

        for rank, (cid, _) in enumerate(dense_res):
            scores[cid] = scores.get(cid, 0) + (1 / (k + rank + 1)) # Equal weight to dense?

        # Sort
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Hydrate
        db = SessionLocal()
        results = []
        try:
            for cid, score in sorted_ids:
                chunk = db.query(Chunk).filter(Chunk.id == cid).first()
                if chunk:
                    paper = db.query(Paper).filter(Paper.id == chunk.paper_id).first()
                    results.append({
                        "chunk_id": chunk.id,
                        "score": score,
                        "text": chunk.text,
                        "section": chunk.section,
                        "paper_title": paper.title if paper else "Unknown",
                        "paper_id": chunk.paper_id
                    })
        finally:
            db.close()

        return results

retriever = RetrievalEngine()
