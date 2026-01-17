import sys
import os
import json
import time
from database import init_db, SessionLocal, Chunk, Entity, Paper

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "ore-backend"))

from core.analysis.graph import graph_engine
from core.analysis.gaps import gap_identifier

# --- Helpers ---
def print_header(title):
    print(f"\n{'='*60}\nSCENARIO: {title}\n{'='*60}")

def print_result(status, message):
    color = "\033[92m" if status == "PASS" else "\033[91m"
    print(f"{color}[{status}] {message}\033[0m")

def clear_test_data():
    db = SessionLocal()
    db.query(Chunk).delete()
    db.query(Entity).delete()
    db.query(Paper).filter(Paper.id >= 100).delete() # Clear test papers
    db.commit()
    db.close()

def inject_entity(name, aliases):
    db = SessionLocal()
    if not db.query(Entity).filter(Entity.canonical_name == name).first():
        e = Entity(canonical_name=name, aliases=json.dumps(aliases), category="General")
        db.add(e)
        db.commit()
    db.close()

def inject_chunk_with_entities(text):
    db = SessionLocal()
    # Ensure Paper 1 exists for chunk
    if not db.query(Paper).filter(Paper.id==1).first():
        p = Paper(id=1, title="Method Paper", filepath_processed="/tmp/mock_1.json")
        db.add(p)
        db.commit()
    c = Chunk(paper_id=1, text=text, section="experiment", token_count=10)
    db.add(c)
    db.commit()
    db.close()

def inject_paper(id, title):
    db = SessionLocal()
    p = db.query(Paper).filter(Paper.id==id).first()
    if p:
        db.delete(p)
        db.commit()

    p = Paper(id=id, title=title, filepath_processed=f"/tmp/mock_{id}.json")
    db.add(p)
    db.commit()
    db.close()

# --- Scenarios ---

def scenario_graph_cycle():
    print_header("1 - Graph Cycle & Load")
    # Inject papers that cite each other with long titles (>4 words)
    t1 = "Analysis of Graph Neural Networks Alpha"
    t2 = "Benchmarking Deep Learning Models Beta"

    inject_paper(101, t1)
    inject_paper(102, t2)

    # Manually overwrite text to ensure citation
    with open("/tmp/mock_101.json", "w") as f:
        # 101 cites 102 (Beta)
        f.write(json.dumps({"sections": {"intro": f"We use ideas from {t2}."}}))
    with open("/tmp/mock_102.json", "w") as f:
        # 102 cites 101 (Alpha)
        f.write(json.dumps({"sections": {"intro": f"We improve upon {t1}."}}))

    res = graph_engine.analyze()
    # Check edges
    edges = res["edges"]
    a_to_b = any(e["source"]==101 and e["target"]==102 for e in edges)
    b_to_a = any(e["source"]==102 and e["target"]==101 for e in edges)

    if a_to_b and b_to_a:
        print_result("PASS", "Cycle detected (A<->B).")
    else:
        print_result("FAIL", f"Edges missing. Found: {edges}")

def scenario_gaps_sparseness():
    print_header("2 - Gap Matrix Sparseness")
    # Inject Method: "Transformer"
    inject_entity("Transformer Model", ["transformer", "self-attention"])
    # Inject Dataset: "ImageNet Dataset"
    inject_entity("ImageNet Dataset", ["imagenet", "ilsvrc"])
    # Inject Dataset: "CIFAR-10 Dataset"
    inject_entity("CIFAR-10 Dataset", ["cifar", "cifar10"])

    # Inject Chunk mentioning Transformer + ImageNet
    inject_chunk_with_entities("We train a Transformer Model on ImageNet Dataset.")

    # Inject Chunk mentioning CNN + CIFAR-10 (making CIFAR-10 active)
    inject_entity("CNN Model", ["cnn"])
    inject_chunk_with_entities("We evaluate CNN Model on CIFAR-10 Dataset.")

    # Expect Gap: Transformer + CIFAR-10 (No chunk mentions both)
    res = gap_identifier.identify_gaps()

    gaps = res["gaps"]
    found_gap = any(g["method"]=="Transformer Model" and g["dataset"]=="CIFAR-10 Dataset" for g in gaps)

    if found_gap:
        print_result("PASS", "Identified Gap: Transformer + CIFAR-10")
    else:
        # Check matrix
        mat = res["matrix"]
        print_result("FAIL", f"Gap not found. Matrix: {mat}")

def main():
    init_db()
    clear_test_data()
    scenario_graph_cycle()
    scenario_gaps_sparseness()

if __name__ == "__main__":
    main()
