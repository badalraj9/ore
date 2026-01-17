import networkx as nx
import community.community_louvain as community_louvain
from sqlalchemy.orm import Session
from database import Paper, SessionLocal
import re
from typing import Dict, Any, List

class CitationGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_graph(self):
        """
        Builds the citation graph from ingested papers.
        Logic:
        1. Nodes = Papers
        2. Edges = Citations (inferred from regex matches in text or explicit metadata if available)
        For MVP, we use regex to find [1], [2] in text, and map to references section.
        Since we don't fully parse references to get DOIs of cited papers (hard),
        we will simulate citations or use a simpler heuristic:
        - If Paper A mentions "Smith et al. (2020)" and Paper B is "Smith et al. (2020)", add edge.
        - OR: Use metadata citations if ArXiv API provided them (ArXiv API doesn't give refs easily).

        Robust MVP approach:
        - Nodes are papers in DB.
        - Edges based on similarity of Title/Authors to Reference strings? Too slow.
        - "Co-Citation" via Entity overlap?

        Let's implement a heuristic:
        If Paper A contains the *Title* of Paper B in its text/references, add edge A->B.
        This is O(N^2) but fine for <100 papers.
        """
        db = SessionLocal()
        try:
            papers = db.query(Paper).all()
            self.graph.clear()

            # Add nodes
            for p in papers:
                self.graph.add_node(p.id, title=p.title, authors=p.authors)

            # Add edges
            for p1 in papers:
                # We need processed text. If strictly from DB 'chunks' could be faster.
                # But let's check raw/processed file?
                # Actually, check if p1.chunks contain p2.title
                # Optimization: Load all titles.
                pass

            # Since reading all chunks is heavy, we'll do a simplified title check
            # using metadata only if titles are unique enough (>5 words).

            titles = {p.id: p.title.lower() for p in papers}

            for p_source in papers:
                # Load text (expensive, maybe just check abstract/chunks?)
                # Checking full text is better.
                # Use processed filepath if available
                if not p_source.filepath_processed: continue

                with open(p_source.filepath_processed, "r") as f:
                    content = f.read().lower()

                for p_target_id, p_target_title in titles.items():
                    if p_source.id == p_target_id: continue

                    # Robustness: Title must be long enough to avoid false positives
                    if len(p_target_title.split()) < 4: continue

                    if p_target_title in content:
                        self.graph.add_edge(p_source.id, p_target_id)

        finally:
            db.close()

    def analyze(self) -> Dict[str, Any]:
        """
        Returns graph metrics: PageRank, Communities.
        """
        if self.graph.number_of_nodes() == 0:
            self.build_graph()

        # PageRank (Influence)
        try:
            pagerank = nx.pagerank(self.graph)
        except:
            pagerank = {n: 0 for n in self.graph.nodes()}

        # Communities (Louvain)
        # Louvain requires undirected graph usually
        undirected = self.graph.to_undirected()
        try:
            partition = community_louvain.best_partition(undirected)
        except:
            partition = {n: 0 for n in self.graph.nodes()}

        # Format output
        nodes = []
        for n in self.graph.nodes():
            nodes.append({
                "id": n,
                "title": self.graph.nodes[n].get("title", "Unknown"),
                "pagerank": pagerank.get(n, 0),
                "community": partition.get(n, 0)
            })

        edges = [{"source": u, "target": v} for u, v in self.graph.edges()]

        return {
            "nodes": nodes,
            "edges": edges,
            "total_papers": len(nodes),
            "total_citations": len(edges)
        }

graph_engine = CitationGraph()
