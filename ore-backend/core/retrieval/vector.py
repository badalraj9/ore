import faiss
import numpy as np
import os
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
from sqlalchemy.orm import Session
from database import Chunk, SessionLocal
from config import settings

class DenseRetriever:
    def __init__(self):
        # Load model (cached)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.chunk_ids = []
        self.is_built = False
        self.index_path = os.path.join(settings.DATA_DIR, "faiss_index.bin")
        self.ids_path = os.path.join(settings.DATA_DIR, "chunk_ids.pkl")

    def build_index(self, force_rebuild: bool = False):
        """
        Builds FAISS index. Loads from disk if available unless force_rebuild.
        """
        if not force_rebuild and os.path.exists(self.index_path) and os.path.exists(self.ids_path):
            print("Loading Dense Index from disk...")
            self.index = faiss.read_index(self.index_path)
            with open(self.ids_path, "rb") as f:
                self.chunk_ids = pickle.load(f)
            self.is_built = True
            return

        print("Building Dense Index from DB...")
        db = SessionLocal()
        try:
            chunks = db.query(Chunk).all()
            if not chunks:
                print("No chunks to embed.")
                return

            self.chunk_ids = [c.id for c in chunks]
            texts = [c.text for c in chunks]

            # Compute embeddings
            embeddings = self.model.encode(texts, convert_to_numpy=True)

            # Initialize Index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)

            # Save
            faiss.write_index(self.index, self.index_path)
            with open(self.ids_path, "wb") as f:
                pickle.dump(self.chunk_ids, f)

            self.is_built = True
            print(f"Dense Index built with {len(chunks)} chunks.")

        finally:
            db.close()

    def search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        if not self.is_built:
            self.build_index()
            if not self.is_built: return []

        query_vector = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_vector, top_k)

        # Convert FAISS indices to Chunk IDs and Distances to Similarity/Score
        # L2 Distance: Lower is better. We convert to 1/(1+d) or just negate for sorting?
        # Score Normalization needed later. Here return raw distance.
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1: continue # Padding
            chunk_id = self.chunk_ids[idx]
            dist = distances[0][i]
            # Convert L2 distance to a score where higher is better
            score = 1.0 / (1.0 + dist)
            results.append((chunk_id, float(score)))

        return results
