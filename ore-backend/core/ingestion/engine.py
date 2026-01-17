import asyncio
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from core.ingestion.fetchers import ArxivFetcher
from database import Paper, SessionLocal
from datetime import datetime
import json
import time

class IngestionEngine:
    def __init__(self):
        self.arxiv = ArxivFetcher()
        self.db_lock = asyncio.Lock() # Basic lock for SQLite safety in async context

    async def ingest(self, query: str, max_results: int = 5):
        """
        Orchestrates the ingestion process:
        1. Search ArXiv
        2. Filter duplicates (check DB)
        3. Download PDFs
        4. Save metadata to DB
        """
        print(f"Starting ingestion for: {query}")

        # 1. Search
        papers = self.arxiv.search(query, max_results)

        # 2. Process
        tasks = []

        for p_data in papers:
            # We must handle DB operations carefully
            paper_id = await self._save_metadata_safe(p_data)

            if paper_id:
                # 3. Download async
                tasks.append(self.process_download(p_data["pdf_url"], str(paper_id)))

        if tasks:
            await asyncio.gather(*tasks)
        print(f"Ingestion complete for: {query}")

    async def _save_metadata_safe(self, p_data: dict) -> int:
        """
        Saves metadata with retry logic for SQLite locking.
        """
        max_retries = 5
        async with self.db_lock:
            for attempt in range(max_retries):
                db = SessionLocal()
                try:
                    # Check duplicate
                    exists = db.query(Paper).filter(Paper.url == p_data["url"]).first()
                    if exists:
                        # print(f"Skipping existing paper: {p_data['title']}")
                        return None

                    # Create DB object
                    paper = Paper(
                        title=p_data["title"],
                        authors=json.dumps(p_data["authors"]),
                        abstract=p_data["abstract"],
                        doi=p_data["doi"],
                        source=p_data["source"],
                        url=p_data["url"],
                        published_date=p_data["published_date"],
                        ingested_at=datetime.utcnow()
                    )
                    db.add(paper)
                    db.commit()
                    db.refresh(paper)
                    return paper.id
                except OperationalError as e:
                    if "locked" in str(e):
                        print(f"Database locked — retrying transaction (Attempt {attempt+1})")
                        time.sleep(0.2 * (attempt + 1))
                        continue
                    else:
                        raise e
                finally:
                    db.close()
        return None

    async def process_download(self, url: str, paper_db_id: str):
        """
        Helper to download and update DB record.
        """
        path = await self.arxiv.download_pdf(url, paper_db_id)
        if path:
            # Update DB
            async with self.db_lock:
                new_db = SessionLocal()
                try:
                    p = new_db.query(Paper).filter(Paper.id == paper_db_id).first()
                    if p:
                        p.filepath_raw = path
                        new_db.commit()
                finally:
                    new_db.close()
            # print(f"Downloaded: {path}")

ingestor = IngestionEngine()
