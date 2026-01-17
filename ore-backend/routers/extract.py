from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from database import SessionLocal, Paper
from core.extraction.extractor import extractor
from config import settings
import os

router = APIRouter()

class ExtractRequest(BaseModel):
    paper_id: int

def run_extraction(paper_id: int):
    db = SessionLocal()
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper or not paper.filepath_raw:
        db.close()
        print(f"Paper {paper_id} not found or no file.")
        return

    try:
        print(f"Extracting content for {paper.title}...")
        out_path = extractor.process(paper.filepath_raw, settings.PROCESSED_DIR)

        # Update DB
        paper.filepath_processed = out_path
        db.commit()
        print(f"Extraction complete: {out_path}")
    except Exception as e:
        print(f"Extraction failed: {e}")
    finally:
        db.close()

@router.post("/process/{paper_id}")
async def process_paper(paper_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_extraction, paper_id)
    return {"message": "Extraction started", "paper_id": paper_id}
