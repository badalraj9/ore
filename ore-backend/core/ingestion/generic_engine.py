import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.exc import OperationalError
from core.ingestion.registry import fetcher_registry
from core.ingestion.webhook import webhook_service
from database import Paper, IngestionTask, SessionLocal, TaskStatusEnum
from config import settings
import time
import os

class GenericIngestionEngine:
    """Generic ingestion engine supporting multiple sources."""
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DOWNLOADS)
    
    async def start_ingestion(
        self, 
        source: str, 
        query: Optional[str] = None,
        url: Optional[str] = None,
        max_results: int = 5,
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new ingestion task and return task_id."""
        task_id = str(uuid.uuid4())
        
        task = IngestionTask(
            task_id=task_id,
            source=source,
            query=query,
            url=url,
            status=TaskStatusEnum.PENDING,
            progress=0,
            webhook_url=webhook_url,
            task_metadata=metadata
        )
        
        db = SessionLocal()
        try:
            db.add(task)
            db.commit()
        finally:
            db.close()
        
        asyncio.create_task(self._process_ingestion(task_id, source, query, url, max_results))
        
        return task_id
    
    async def _process_ingestion(
        self, 
        task_id: str, 
        source: str, 
        query: Optional[str],
        url: Optional[str],
        max_results: int
    ):
        """Process the ingestion task."""
        db = SessionLocal()
        try:
            task = db.query(IngestionTask).filter(IngestionTask.task_id == task_id).first()
            if not task:
                return
            
            task.status = TaskStatusEnum.PROCESSING
            task.progress = 10
            task.message = "Starting ingestion..."
            db.commit()
            
            if webhook_url := task.webhook_url:
                webhook_service.send_progress(webhook_url, task_id, 10, "Starting ingestion")
            
            fetcher = fetcher_registry.get(source)
            if not fetcher:
                raise ValueError(f"Unknown source: {source}")
            
            if query:
                results = fetcher.search(query, max_results)
            elif url:
                metadata = fetcher.fetch_metadata(url)
                results = [metadata] if metadata else []
            else:
                raise ValueError("Either query or url must be provided")
            
            task.progress = 30
            task.message = f"Found {len(results)} documents"
            db.commit()
            
            if webhook_url := task.webhook_url:
                webhook_service.send_progress(webhook_url, task_id, 30, f"Found {len(results)} documents")
            
            papers = []
            for i, p_data in enumerate(results):
                paper_id = await self._save_paper_metadata(p_data, db)
                if paper_id:
                    papers.append({"paper_id": paper_id, "data": p_data})
                
                progress = 30 + int((i + 1) / len(results) * 30)
                task.progress = progress
                task.message = f"Processing document {i+1}/{len(results)}"
                db.commit()
            
            task.progress = 70
            task.message = "Downloading files..."
            db.commit()
            
            if webhook_url := task.webhook_url:
                webhook_service.send_progress(webhook_url, task_id, 70, "Downloading files")
            
            for i, paper in enumerate(papers):
                await self._download_and_update(paper["data"], str(paper["paper_id"]), db)
                
                progress = 70 + int((i + 1) / len(papers) * 25)
                task.progress = progress
                task.message = f"Downloaded {i+1}/{len(papers)} files"
                db.commit()
            
            task.status = TaskStatusEnum.COMPLETED
            task.progress = 100
            task.message = "Ingestion complete"
            task.result = {"papers_ingested": len(papers), "source": source}
            db.commit()
            
            if webhook_url := task.webhook_url:
                webhook_service.send_task_complete(webhook_url, task_id, task.result)
                
        except Exception as e:
            task = db.query(IngestionTask).filter(IngestionTask.task_id == task_id).first()
            if task:
                task.status = TaskStatusEnum.FAILED
                task.error_detail = str(e)
                task.message = f"Failed: {str(e)}"
                db.commit()
                
                if webhook_url := task.webhook_url:
                    webhook_service.send_task_failed(webhook_url, task_id, str(e))
        finally:
            db.close()
    
    async def _save_paper_metadata(self, p_data: dict, db) -> Optional[int]:
        """Save paper metadata to database."""
        for attempt in range(settings.MAX_INGEST_RETRIES):
            try:
                exists = db.query(Paper).filter(Paper.url == p_data["url"]).first()
                if exists:
                    return exists.id
                
                paper = Paper(
                    title=p_data.get("title", "Unknown"),
                    authors=json.dumps(p_data.get("authors", [])),
                    abstract=p_data.get("abstract", ""),
                    doi=p_data.get("doi"),
                    source=p_data.get("source", "unknown"),
                    url=p_data.get("url"),
                    published_date=p_data.get("published_date"),
                    ingested_at=datetime.utcnow()
                )
                db.add(paper)
                db.commit()
                db.refresh(paper)
                return paper.id
            except OperationalError as e:
                if "locked" in str(e):
                    time.sleep(0.2 * (attempt + 1))
                    continue
                raise
        return None
    
    async def _download_and_update(self, p_data: dict, paper_id: str, db):
        """Download file and update paper record."""
        if pdf_url := p_data.get("pdf_url"):
            async with self.semaphore:
                fetcher = fetcher_registry.get(p_data.get("source", "arxiv"))
                if fetcher:
                    path = await fetcher.download_pdf(pdf_url, paper_id)
                    if path:
                        paper = db.query(Paper).filter(Paper.id == paper_id).first()
                        if paper:
                            paper.filepath_raw = path
                            db.commit()
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an ingestion task."""
        db = SessionLocal()
        try:
            task = db.query(IngestionTask).filter(IngestionTask.task_id == task_id).first()
            if not task:
                return None
            
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "progress": task.progress,
                "message": task.message,
                "result": task.result,
                "error_detail": task.error_detail,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            }
        finally:
            db.close()
    
    def list_tasks(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all ingestion tasks."""
        db = SessionLocal()
        try:
            tasks = db.query(IngestionTask).order_by(
                IngestionTask.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return [{
                "task_id": t.task_id,
                "source": t.source,
                "status": t.status.value,
                "progress": t.progress,
                "message": t.message,
                "created_at": t.created_at.isoformat() if t.created_at else None
            } for t in tasks]
        finally:
            db.close()

ingestion_engine = GenericIngestionEngine()
