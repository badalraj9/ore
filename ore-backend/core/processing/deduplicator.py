from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from database import Paper, Chunk, SessionLocal
import json
import collections
import re
import string

class Deduplicator:
    def __init__(self):
        self.doc_threshold = 0.9
        self.chunk_threshold = 0.85 # Scenario 3: Near-duplicate

    def cosine_similarity(self, str1: str, str2: str) -> float:
        """
        Scenario 3: Better similarity metric than Jaccard for text.
        Simple manual implementation to remain LLM-free/StdLib.
        """
        # Tokenize and count, stripping punctuation
        def tokenize(text):
            # Remove punctuation
            text = text.translate(str.maketrans('', '', string.punctuation))
            return text.lower().split()

        vec1 = collections.Counter(tokenize(str1))
        vec2 = collections.Counter(tokenize(str2))

        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])

        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = (sum1**0.5) * (sum2**0.5)

        if not denominator:
            return 0.0
        return float(numerator) / denominator

    def is_duplicate_paper(self, title: str, abstract: str, db: Session) -> bool:
        """
        Checks if a paper is a duplicate based on fuzzy title/abstract match.
        """
        existing_papers = db.query(Paper).all()
        for p in existing_papers:
            # Title match
            if SequenceMatcher(None, title, p.title).ratio() > self.doc_threshold:
                return True
            # Abstract match (start of abstract)
            if abstract and p.abstract:
                if SequenceMatcher(None, abstract[:500], p.abstract[:500]).ratio() > self.doc_threshold:
                    return True
        return False

    def deduplicate_chunks(self, paper_id: int):
        """
        Flags or removes duplicate chunks within a paper.
        Scenario 8: Determinism preserved by processing sorted chunks (by ID).
        """
        db = SessionLocal()
        try:
            # Order by ID ensures we always keep the first one
            chunks = db.query(Chunk).filter(Chunk.paper_id == paper_id).order_by(Chunk.id).all()
            to_delete = []

            # Simple pairwise check O(N^2) - OK for <100 chunks per paper
            for i in range(len(chunks)):
                if chunks[i].id in to_delete: continue

                for j in range(i + 1, len(chunks)):
                    if chunks[j].id in to_delete: continue

                    c1 = chunks[i]
                    c2 = chunks[j]

                    # Scenario 7: Redundant Sentences (Cosine Sim)
                    sim = self.cosine_similarity(c1.text, c2.text)
                    if sim > self.chunk_threshold:
                        # Mark c2 for deletion (keep c1)
                        # print(f"Duplicate chunk found: {c2.id} is similar to {c1.id} ({sim:.2f})")
                        to_delete.append(c2.id)

            if to_delete:
                db.query(Chunk).filter(Chunk.id.in_(to_delete)).delete(synchronize_session=False)
                db.commit()
                # print(f"Removed {len(to_delete)} duplicate chunks for paper {paper_id}")

        finally:
            db.close()

deduplicator = Deduplicator()
