from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from core.analysis.clustering import clusterer
from core.analysis.contradiction import contradiction_detector
from core.analysis.graph import graph_engine
from core.analysis.gaps import gap_identifier

router = APIRouter()

class ClusterRequest(BaseModel):
    paper_id: int = None
    k: int = 5

class ContradictionRequest(BaseModel):
    query: str

@router.post("/cluster")
async def cluster(request: ClusterRequest):
    return clusterer.cluster_chunks(request.paper_id, request.k)

@router.post("/contradiction")
async def detect_contradiction(request: ContradictionRequest):
    return contradiction_detector.detect_contradictions(request.query)

@router.post("/graph")
async def analyze_graph():
    return graph_engine.analyze()

@router.post("/gaps")
async def identify_gaps():
    return gap_identifier.identify_gaps()
