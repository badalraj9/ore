from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from core.query_engine import processor

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    original_query: str
    intent: str
    entities: List[Dict[str, str]]
    keywords: List[str]
    expanded_terms: List[str]

@router.post("/analyze", response_model=QueryResponse)
async def analyze_query(request: QueryRequest):
    try:
        result = processor.process(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
