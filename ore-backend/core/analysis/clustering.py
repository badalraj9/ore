from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session
from database import Chunk, SessionLocal
from typing import List, Dict, Any
from config import settings
import numpy as np

class ClusterEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)

    def cluster_chunks(self, paper_id: int = None, k: int = None) -> Dict[int, List[str]]:
        """Clusters chunks into K topics using TF-IDF + KMeans."""
        k = k or settings.DEFAULT_CLUSTERS
        
        db = SessionLocal()
        try:
            query = db.query(Chunk)
            if paper_id:
                query = query.filter(Chunk.paper_id == paper_id)
            chunks = query.all()

            if not chunks:
                return {}

            unique_texts = sorted(list(set([c.text for c in chunks])))

            if not unique_texts:
                return {}

            tfidf_matrix = self.vectorizer.fit_transform(unique_texts)

            n_clusters = min(k, len(unique_texts))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(tfidf_matrix)

            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            terms = self.vectorizer.get_feature_names_out()

            cluster_map = {}
            for i in range(n_clusters):
                top_terms = [terms[ind] for ind in order_centroids[i, :settings.MAX_CLUSTER_KEYWORDS]]
                cluster_map[i] = top_terms

            return cluster_map

        except Exception as e:
            return {}
        finally:
            db.close()

clusterer = ClusterEngine()
