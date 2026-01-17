import sys
import os
import asyncio

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "ore-backend"))

from core.ingestion.engine import ingestor
from database import init_db

async def test_ingestion():
    # Initialize DB for test
    init_db()
    # Ingest a small number of papers on a specific topic
    await ingestor.ingest("RAG hallucination", max_results=2)

if __name__ == "__main__":
    asyncio.run(test_ingestion())
