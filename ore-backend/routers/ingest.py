from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from core.ingestion.engine import ingestor

router = APIRouter()

class IngestRequest(BaseModel):
    query: str
    max_results: int = 5

@router.post("/start")
async def start_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Starts an async background ingestion task.
    """
    background_tasks.add_task(ingestor.ingest, request.query, request.max_results)
    return {"message": "Ingestion started in background", "query": request.query}
