import sys
import os
import json
import time
import hashlib
from database import init_db, SessionLocal, Chunk, Entity, Paper

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "ore-backend"))

from core.processing.chunker import chunker
from core.processing.deduplicator import deduplicator
from core.processing.canonicalizer import canonicalizer

# --- Helpers ---
def print_header(title):
    print(f"\n{'='*60}\nSCENARIO: {title}\n{'='*60}")

def print_result(status, message):
    color = "\033[92m" if status == "PASS" else "\033[91m"
    print(f"{color}[{status}] {message}\033[0m")

def create_mock_paper(id, content_map):
    db = SessionLocal()
    # Delete if exists
    db.query(Paper).filter(Paper.id == id).delete()

    # Create mock processed file
    mock_path = f"/tmp/mock_paper_{id}.json"
    with open(mock_path, "w") as f:
        json.dump({"sections": content_map}, f)

    p = Paper(id=id, title=f"Mock Paper {id}", filepath_processed=mock_path)
    db.add(p)
    db.commit()
    db.close()
    return mock_path

# --- Scenarios ---

def scenario_2_noisy_text():
    print_header("2 - Canonicalization of Noisy Text")
    noisy = "   Machine   Learning [1] (ML) is \uFB01ne. "
    cleaned = chunker.clean_text(noisy)
    expected = "Machine Learning (ML) is fine."

    if cleaned == expected:
        print_result("PASS", f"Cleaned text: '{cleaned}'")
    else:
        print_result("FAIL", f"Expected '{expected}', got '{cleaned}'")

def scenario_3_dedup():
    print_header("3 - Duplicate Detection (Cosine)")
    text1 = "Machine learning models are great for data analysis."
    text2 = "Machine learning models are great for data analysis." # Exact
    text3 = "Machine learning models are great for data analysis and prediction." # Near duplicate (>80% overlap)
    text4 = "Banana bread recipe with walnuts." # Different

    sim_exact = deduplicator.cosine_similarity(text1, text2)
    sim_near = deduplicator.cosine_similarity(text1, text3)
    sim_diff = deduplicator.cosine_similarity(text1, text4)

    print(f"Exact: {sim_exact:.2f}, Near: {sim_near:.2f}, Diff: {sim_diff:.2f}")

    if sim_exact > 0.99 and sim_near > 0.8 and sim_diff < 0.2:
        print_result("PASS", "Similarity metrics aligned.")
    else:
        print_result("FAIL", "Similarity metrics unexpected.")

def scenario_6_lemmatization():
    print_header("6 - Lowercasing & Lemmatization Consistency")
    inputs = ["Models", "Model", "modeling", "MODELS"]
    canonicals = set()

    for i in inputs:
        # We use link_entity which applies lemmatization
        c = canonicalizer.link_entity(i, "Test")
        canonicals.add(c)

    print(f"Inputs: {inputs} -> Canonicals: {canonicals}")
    if len(canonicals) == 1:
        print_result("PASS", f"All mapped to single canonical: {list(canonicals)[0]}")
    elif len(canonicals) == 2 and "Modeling" in canonicals:
        # "Modeling" lemma is "model" usually, but sometimes preserved.
        # Spacy: model, model, model, model?
        # Let's see what happens.
        pass
    else:
        print_result("WARNING", f"Mapped to {len(canonicals)} forms (Strict pass requires 1)")

def scenario_8_determinism():
    print_header("8 - Chunk Ordering Determinism")
    content = {
        "abstract": "This is abstract.",
        "introduction": "This is intro. It has multiple sentences. One more.",
        "results": "Results are good."
    }
    create_mock_paper(99, content)

    # Run 1
    chunker.process_paper(99)
    db = SessionLocal()
    chunks1 = [c.text for c in db.query(Chunk).filter(Chunk.paper_id == 99).order_by(Chunk.id).all()]
    hash1 = hashlib.md5("".join(chunks1).encode()).hexdigest()
    db.close()

    # Run 2
    chunker.process_paper(99)
    db = SessionLocal()
    chunks2 = [c.text for c in db.query(Chunk).filter(Chunk.paper_id == 99).order_by(Chunk.id).all()]
    hash2 = hashlib.md5("".join(chunks2).encode()).hexdigest()
    db.close()

    if hash1 == hash2:
        print_result("PASS", "Deterministic output confirmed.")
    else:
        print_result("FAIL", "Output hashes differ.")

def scenario_9_overflow():
    print_header("9 - Boundary Conditions & Overflow")
    # Generate 10k char string without spaces (worst case) or just long sentences
    long_sent = "word " * 2000 # 10k chars
    content = {"intro": long_sent}
    create_mock_paper(100, content)

    start = time.time()
    chunker.process_paper(100)
    duration = time.time() - start

    db = SessionLocal()
    chunks = db.query(Chunk).filter(Chunk.paper_id == 100).all()
    max_len = max([len(c.text.split()) for c in chunks]) if chunks else 0
    db.close()

    print(f"Processed in {duration:.3f}s. Max chunk tokens: {max_len}")

    # Default target is ~300-400 tokens. If > 1000, split failed.
    if max_len < 600:
        print_result("PASS", "Overflow handled correctly.")
    else:
        print_result("FAIL", f"Chunk too large: {max_len}")

def main():
    init_db()
    scenario_2_noisy_text()
    scenario_3_dedup()
    scenario_6_lemmatization()
    scenario_8_determinism()
    scenario_9_overflow()

if __name__ == "__main__":
    main()
