from fastapi import APIRouter, HTTPException
from schemas import SearchRequest, SearchResponse, PaginatedResponse
from core.retrieval.engine import retriever
from config import settings

router = APIRouter()

@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    results = retriever.search(request.query, request.top_k)
    return SearchResponse(
        results=results,
        total=len(results),
        query=request.query
    )

@router.get("/")
async def search_get(q: str, top_k: int = settings.DEFAULT_TOP_K):
    """GET endpoint for search."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    results = retriever.search(q, top_k)
    return SearchResponse(
        results=results,
        total=len(results),
        query=q
    )
