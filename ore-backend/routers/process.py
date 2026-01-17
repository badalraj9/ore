from fastapi import APIRouter, BackgroundTasks, HTTPException
from core.processing.chunker import chunker
from core.processing.deduplicator import deduplicator
from core.processing.canonicalizer import canonicalizer
from database import SessionLocal, Chunk

router = APIRouter()

def run_processing_pipeline(paper_id: int):
    print(f"Starting Phase 4 pipeline for Paper {paper_id}")

    # 1. Chunking
    chunker.process_paper(paper_id)

    # 2. Deduplication (Chunk level)
    deduplicator.deduplicate_chunks(paper_id)

    # 3. Canonicalization
    # We scan all chunks for entities
    db = SessionLocal()
    chunks = db.query(Chunk).filter(Chunk.paper_id == paper_id).all()
    for chunk in chunks:
        canonicalizer.process_chunk_entities(chunk.text)
    db.close()

    print(f"Phase 4 pipeline complete for Paper {paper_id}")

@router.post("/{paper_id}")
async def process_paper(paper_id: int, background_tasks: BackgroundTasks):
    """
    Triggers Phase 4: Chunking, Deduplication, Canonicalization.
    """
    background_tasks.add_task(run_processing_pipeline, paper_id)
    return {"message": "Processing pipeline started", "paper_id": paper_id}
