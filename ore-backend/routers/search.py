from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Any
from core.retrieval.engine import retriever

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10

@router.post("/")
async def search(request: SearchRequest):
    results = retriever.search(request.query, request.top_k)
    return results
