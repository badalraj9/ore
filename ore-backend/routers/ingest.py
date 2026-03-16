from fastapi import APIRouter, BackgroundTasks, HTTPException
from schemas import IngestRequest, IngestResponse, TaskStatusResponse, IngestSource
from core.ingestion.generic_engine import ingestion_engine
from core.ingestion.registry import fetcher_registry

router = APIRouter()

@router.post("/start", response_model=IngestResponse)
async def start_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Start a generic ingestion task from any supported source.
    """
    available_sources = fetcher_registry.list_sources()
    if request.source.value not in available_sources:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown source. Available: {available_sources}"
        )
    
    task_id = await ingestion_engine.start_ingestion(
        source=request.source.value,
        query=request.query,
        url=request.url,
        max_results=request.max_results,
        webhook_url=request.webhook_url,
        metadata=request.metadata
    )
    
    return IngestResponse(
        task_id=task_id,
        status="pending",
        message="Ingestion task started"
    )

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get status of an ingestion task."""
    status = ingestion_engine.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(**status)

@router.get("/tasks")
async def list_tasks(limit: int = 50, offset: int = 0):
    """List all ingestion tasks."""
    tasks = ingestion_engine.list_tasks(limit, offset)
    return {"tasks": tasks, "count": len(tasks)}

@router.get("/sources")
async def list_sources():
    """List all available ingestion sources."""
    sources = fetcher_registry.list_sources()
    return {"sources": sources}
