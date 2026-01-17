import sys
import os
import json
import time
import hashlib
from database import init_db, SessionLocal, Chunk, Entity, Paper

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "ore-backend"))

from core.retrieval.engine import retriever
from core.analysis.clustering import clusterer
from core.analysis.contradiction import contradiction_detector

# --- Helpers ---
def print_header(title):
    print(f"\n{'='*60}\nSCENARIO: {title}\n{'='*60}")

def print_result(status, message):
    color = "\033[92m" if status == "PASS" else "\033[91m"
    print(f"{color}[{status}] {message}\033[0m")

def inject_chunk(text, section="stress_test"):
    db = SessionLocal()
    c = Chunk(paper_id=1, text=text, section=section, token_count=len(text.split()))
    db.add(c)
    db.commit()
    db.refresh(c)
    db.close()
    return c.id

def clear_stress_chunks():
    db = SessionLocal()
    db.query(Chunk).filter(Chunk.section == "stress_test").delete()
    db.commit()
    db.close()

# --- Scenarios ---

def scenario_1_poisoned_corpus():
    print_header("1 - Poisoned Corpus Attack")
    # Inject spam
    spam_id = inject_chunk("RAG " * 50 + "improves " * 10)
    real_id = inject_chunk("RAG improves performance on QA tasks.")

    # Rebuild index
    retriever.sparse.build_index()

    # Search
    results = retriever.search("RAG improves", top_k=10)
    top_ids = [r["chunk_id"] for r in results]

    if real_id in top_ids:
        # Check rank
        real_rank = top_ids.index(real_id)
        spam_rank = top_ids.index(spam_id) if spam_id in top_ids else 999

        if real_rank < spam_rank:
             print_result("PASS", "Real chunk outranks spam.")
        else:
             print_result("FAIL", f"Spam {spam_rank} > Real {real_rank}")
    else:
        print_result("FAIL", "Real chunk not found.")

def scenario_5_cluster_collapse():
    print_header("5 - Cluster Collapse Attack")
    # Inject duplicate chunks
    text = "Neural networks are deep learning models."
    for _ in range(50):
        inject_chunk(text)

    # Cluster
    clusters = clusterer.cluster_chunks(paper_id=1, k=3)

    # Should not have 1 massive cluster dominating if dedup works?
    # Actually, deduplication in `cluster_chunks` removes exact duplicates from INPUT to KMeans.
    # So KMeans sees 1 instance of this text.
    # Result: It should form a cluster, but not "collapse" everything else into it if there are other chunks.
    # We assume Paper 1 has other chunks from previous tests.

    print(f"Clusters: {clusters}")
    if len(clusters) >= 2:
        print_result("PASS", f"Clusters maintained diversity: {len(clusters)}")
    else:
        print_result("FAIL", "Collapsed to single cluster.")

def scenario_7_partial_info():
    print_header("7 - Partial Information (False Positive)")
    # Inject vague chunks
    id1 = inject_chunk("RAG is generally effective.")
    id2 = inject_chunk("Fine-tuning is useful.")

    # Detect
    cons = contradiction_detector.detect_contradictions("RAG fine-tuning")

    # Check if these two are flagged
    flagged = False
    for c in cons:
        t1 = c["claim_1"]["text"]
        t2 = c["claim_2"]["text"]
        if "generally effective" in t1 and "useful" in t2:
            flagged = True

    if not flagged:
        print_result("PASS", "No false contradiction on vague statements.")
    else:
        print_result("FAIL", "False contradiction detected.")

def scenario_9_determinism():
    print_header("9 - Deterministic Replay")
    query = "RAG"

    res1 = retriever.search(query, top_k=5)
    res2 = retriever.search(query, top_k=5)

    ids1 = [r["chunk_id"] for r in res1]
    ids2 = [r["chunk_id"] for r in res2]

    if ids1 == ids2:
        print_result("PASS", "Retrieval is deterministic.")
    else:
        print_result("FAIL", f"Retrieval Drift: {ids1} vs {ids2}")

    # Check Cluster Determinism
    c1 = clusterer.cluster_chunks(paper_id=1, k=3)
    c2 = clusterer.cluster_chunks(paper_id=1, k=3)
    if c1 == c2:
        print_result("PASS", "Clustering is deterministic.")
    else:
        print_result("FAIL", "Clustering Drift.")

def main():
    init_db()
    # Cleanup before start
    clear_stress_chunks()

    scenario_1_poisoned_corpus()
    scenario_5_cluster_collapse()
    scenario_7_partial_info()
    scenario_9_determinism()

    # Cleanup after
    clear_stress_chunks()

if __name__ == "__main__":
    main()
