from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session
from database import Chunk, SessionLocal
from typing import List, Dict, Any
import numpy as np
import collections

class ClusterEngine:
    def __init__(self):
        # Scenario 4: Topic blending requires robust stop words
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)

    def cluster_chunks(self, paper_id: int = None, k: int = 5) -> Dict[int, List[str]]:
        """
        Clusters chunks (optionally filtered by paper) into K topics.
        Returns: {cluster_id: [top_keywords]}
        """
        db = SessionLocal()
        try:
            query = db.query(Chunk)
            if paper_id:
                query = query.filter(Chunk.paper_id == paper_id)
            chunks = query.all()

            if not chunks:
                return {}

            # Scenario 5: Cluster Collapse Attack (Deduplicate before clustering)
            # Simple deduplication by text content to prevent one repeated chunk from dominating
            unique_texts = sorted(list(set([c.text for c in chunks])))

            if not unique_texts:
                return {}

            # TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform(unique_texts)

            # KMeans
            # Handle case where n_samples < k
            n_clusters = min(k, len(unique_texts))
            # Fixed random_state for Scenario 9 (Determinism)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(tfidf_matrix)

            # Extract keywords per cluster
            # Get centroids
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            terms = self.vectorizer.get_feature_names_out()

            cluster_map = {}
            for i in range(n_clusters):
                top_terms = [terms[ind] for ind in order_centroids[i, :5]]
                cluster_map[i] = top_terms

            return cluster_map

        except Exception as e:
            # print(f"Clustering error: {e}")
            return {}
        finally:
            db.close()

clusterer = ClusterEngine()
