import sys
import os
import json
from sqlalchemy.orm import Session

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "ore-backend"))

from database import init_db, SessionLocal, Paper, Chunk
from core.retrieval.engine import retriever
from core.analysis.clustering import clusterer
from core.analysis.contradiction import contradiction_detector

def test_phases_5_7():
    print("--- Testing Phases 5-7 ---")

    init_db()
    db = SessionLocal()

    # 0. Setup: Ensure we have data (from previous phases)
    # Also inject fake contradictions for Phase 7 test
    paper = db.query(Paper).first()
    if not paper:
        print("No papers found. Please run previous phase tests first.")
        return

    # Inject Fake Contradiction Chunks
    # Chunk A: RAG outperforms fine-tuning.
    # Chunk B: RAG performs worse than fine-tuning.
    c1 = Chunk(paper_id=paper.id, text="RAG significantly outperforms fine-tuning in knowledge retrieval tasks.", section="results", token_count=10)
    c2 = Chunk(paper_id=paper.id, text="However, RAG performs worse than fine-tuning when knowledge is static.", section="discussion", token_count=10)
    db.add(c1)
    db.add(c2)
    db.commit()
    print("Injected fake contradiction chunks.")

    # 1. Test Retrieval (Index Build + Search)
    print("\n[Phase 5] Building Index and Searching 'RAG'...")
    # Trigger build implicitly via search
    results = retriever.search("RAG outperforms", top_k=5)
    print(f"Found {len(results)} results.")
    for res in results:
        print(f"- ({res['score']:.4f}) {res['text'][:80]}...")

    # 2. Test Clustering
    print("\n[Phase 6] Clustering Paper 1...")
    clusters = clusterer.cluster_chunks(paper_id=paper.id, k=3)
    for cid, keywords in clusters.items():
        print(f"Cluster {cid}: {keywords}")

    # 3. Test Contradiction
    print("\n[Phase 7] Detecting Contradictions for 'RAG performance'...")
    contradictions = contradiction_detector.detect_contradictions("RAG performance")
    print(f"Found {len(contradictions)} contradictions.")
    for con in contradictions:
        print(f"CONFLICT: {con['claim_1']['text']} (Pol: {con['claim_1']['polarity']})")
        print(f"      VS: {con['claim_2']['text']} (Pol: {con['claim_2']['polarity']})")

    # Cleanup fake chunks
    db.delete(c1)
    db.delete(c2)
    db.commit()
    db.close()

if __name__ == "__main__":
    test_phases_5_7()
