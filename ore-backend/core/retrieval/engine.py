from typing import List, Dict, Any
from core.retrieval.bm25 import SparseRetriever
from core.retrieval.vector import DenseRetriever
from database import SessionLocal, Chunk, Paper
from config import settings

class RetrievalEngine:
    def __init__(self):
        self.sparse = SparseRetriever()
        self.dense = DenseRetriever()

    def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Hybrid Search using RRF with configurable weights."""
        top_k = top_k or settings.DEFAULT_TOP_K
        
        sparse_res = self.sparse.search(query, top_k=top_k*2)
        dense_res = self.dense.search(query, top_k=top_k*2)

        scores = {}
        k = settings.RRF_K

        for rank, (cid, _) in enumerate(sparse_res):
            scores[cid] = scores.get(cid, 0) + (settings.SPARSE_WEIGHT / (k + rank + 1))

        for rank, (cid, _) in enumerate(dense_res):
            scores[cid] = scores.get(cid, 0) + (settings.DENSE_WEIGHT / (k + rank + 1))

        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

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
