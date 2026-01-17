from sqlalchemy.orm import Session
from database import Entity, SessionLocal, Chunk
import json
from typing import List, Dict, Any
import collections

class GapIdentifier:
    def __init__(self):
        self.method_keywords = {"method", "model", "algorithm", "network", "transformer", "architecture", "approach"}
        self.dataset_keywords = {"dataset", "corpus", "benchmark", "bank", "collection", "set"}

    def infer_category(self, entity_name: str, aliases: List[str]) -> str:
        text = (entity_name + " " + " ".join(aliases)).lower()
        if any(k in text for k in self.dataset_keywords):
            return "Dataset"
        if any(k in text for k in self.method_keywords):
            return "Method"
        return "Other"

    def identify_gaps(self) -> Dict[str, Any]:
        """
        Builds Method-Dataset matrix and finds zeroes.
        """
        db = SessionLocal()
        try:
            # 1. Identify Methods and Datasets
            entities = db.query(Entity).all()
            methods = []
            datasets = []

            ent_map = {} # canonical -> category

            for ent in entities:
                aliases = json.loads(ent.aliases)
                cat = self.infer_category(ent.canonical_name, aliases)
                ent_map[ent.canonical_name] = cat
                if cat == "Method":
                    methods.append(ent.canonical_name)
                elif cat == "Dataset":
                    datasets.append(ent.canonical_name)

            # 2. Build Co-occurrence Matrix
            # Scan chunks. If a chunk mentions Method M and Dataset D, increment count.
            matrix = collections.defaultdict(lambda: collections.defaultdict(int))

            chunks = db.query(Chunk).all()
            for chunk in chunks:
                text = chunk.text.lower()

                # Check presence (naive O(M*D) per chunk? Too slow.)
                # Optimization: Check found entities in this chunk from Phase 4?
                # For now, just scan top methods/datasets

                found_methods = [m for m in methods if m.lower() in text]
                found_datasets = [d for d in datasets if d.lower() in text]

                for m in found_methods:
                    for d in found_datasets:
                        matrix[m][d] += 1

            # 3. Find Gaps (Top methods vs Top datasets)
            # Filter to active ones to avoid noise
            active_methods = [m for m in methods if sum(matrix[m].values()) > 0]
            active_datasets = [d for d in datasets if sum(row[d] for row in matrix.values()) > 0]

            gaps = []
            for m in active_methods:
                for d in active_datasets:
                    if matrix[m][d] == 0:
                        gaps.append({
                            "method": m,
                            "dataset": d,
                            "reason": "No co-occurrence found in corpus."
                        })

            # Sort gaps by "potential" (e.g. popular method + popular dataset = high potential gap)
            # Not implemented in MVP.

            return {
                "matrix": {m: {d: matrix[m][d] for d in active_datasets} for m in active_methods},
                "gaps": gaps[:20], # Return top 20 gaps
                "methods": active_methods,
                "datasets": active_datasets
            }

        finally:
            db.close()

gap_identifier = GapIdentifier()
