from rank_bm25 import BM25Okapi
from typing import List, Tuple
from sqlalchemy.orm import Session
from database import Chunk, SessionLocal
import re
import collections

class SparseRetriever:
    def __init__(self):
        self.bm25 = None
        self.chunk_ids = [] # Map index to chunk_id
        self.chunk_texts = [] # Store texts for spam check
        self.is_built = False

    def tokenize(self, text: str) -> List[str]:
        # Simple tokenization
        text = text.lower()
        return [t for t in re.split(r'\W+', text) if t]

    def is_spam(self, text: str) -> bool:
        """
        Scenario 1: Detect keyword spam (low lexical diversity).
        """
        tokens = self.tokenize(text)
        if not tokens: return False
        unique_ratio = len(set(tokens)) / len(tokens)
        # "RAG " * 50 -> 1 unique / 50 total = 0.02.
        # "Normal sentence" -> 1.0 or high.
        return unique_ratio < 0.2

    def build_index(self):
        """
        Loads all chunks from DB and builds BM25 index in memory.
        """
        db = SessionLocal()
        try:
            chunks = db.query(Chunk).all()
            if not chunks:
                return

            self.chunk_ids = [c.id for c in chunks]
            self.chunk_texts = [c.text for c in chunks] # Cache text for filtering
            corpus = [self.tokenize(c.text) for c in chunks]
            self.bm25 = BM25Okapi(corpus)
            self.is_built = True
        finally:
            db.close()

    def search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """
        Returns list of (chunk_id, score).
        """
        if not self.is_built:
            self.build_index()
            if not self.is_built: return []

        tokenized_query = self.tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        scored_chunks = []
        for i, score in enumerate(scores):
            # Scenario 1: Filter Spam
            if self.is_spam(self.chunk_texts[i]):
                # Penalize heavily or exclude
                score = score * 0.01

            scored_chunks.append((self.chunk_ids[i], score))

        # Sort desc
        top_results = sorted(scored_chunks, key=lambda x: x[1], reverse=True)[:top_k]
        return top_results
