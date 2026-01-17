import sys
import os
import json
from sqlalchemy.orm import Session

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "ore-backend"))

from database import init_db, SessionLocal, Paper, Chunk, Entity
from core.processing.chunker import chunker
from core.processing.canonicalizer import canonicalizer
from core.processing.deduplicator import deduplicator
from routers.process import run_processing_pipeline

def test_phase4():
    print("--- Testing Phase 4 ---")

    # Initialize DB (Schema update)
    init_db()
    db = SessionLocal()

    # Get paper from Phase 3 (ID 1)
    paper = db.query(Paper).filter(Paper.id == 1).first()
    if not paper:
        print("Paper 1 not found. Run test_ingest.py and test_extract.py first.")
        return

    print(f"Processing Paper: {paper.title}")

    # Ensure extraction is done and DB updated
    if not paper.filepath_processed and paper.filepath_raw:
        from core.extraction.extractor import extractor
        from config import settings
        print("Running missing extraction step...")
        out_path = extractor.process(paper.filepath_raw, settings.PROCESSED_DIR)
        paper.filepath_processed = out_path
        db.commit()
        print(f"Updated DB with processed path: {out_path}")

    # Run Pipeline synchronously
    run_processing_pipeline(paper.id)

    # Verify Chunks
    chunks = db.query(Chunk).filter(Chunk.paper_id == paper.id).all()
    print(f"\nChunks Created: {len(chunks)}")
    if chunks:
        print(f"Sample Chunk ({chunks[0].section}): {chunks[0].text[:100]}...")

    # Verify Entities
    entities = db.query(Entity).all()
    print(f"\nEntities Found: {len(entities)}")
    for ent in entities:
        print(f"- {ent.canonical_name} (Aliases: {ent.aliases})")

    # Test Deduplication logic manually
    print("\n--- Testing Deduplication Logic ---")
    sim = deduplicator.jaccard_similarity("Machine learning is great", "Machine learning is awesome")
    print(f"Similarity 'great' vs 'awesome': {sim:.2f}")

    # Test Canonicalizer Logic manually
    print("\n--- Testing Canonicalizer Logic ---")
    text = "The Large Language Model (LLM) is useful. Another LLM is GPT."
    canonicalizer.process_chunk_entities(text)
    # Check if LLM linked to Large Language Model
    ent = db.query(Entity).filter(Entity.canonical_name == "Large Language Model").first()
    if ent:
        print(f"Found Entity: {ent.canonical_name}, Aliases: {ent.aliases}")
    else:
        print("Entity 'Large Language Model' not found.")

    db.close()

if __name__ == "__main__":
    test_phase4()
