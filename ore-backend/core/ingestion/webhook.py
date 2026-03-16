import aiohttp
import asyncio
from typing import Optional, Dict, Any
from config import settings
import json
import logging

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for sending webhook notifications."""
    
    async def send(self, url: str, payload: Dict[str, Any], timeout: int = None):
        """Send webhook notification."""
        if not url:
            return
        
        timeout = timeout or settings.WEBHOOK_TIMEOUT
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    json=payload, 
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status < 400:
                        logger.info(f"Webhook sent successfully to {url}")
                    else:
                        logger.warning(f"Webhook failed: {response.status}")
        except asyncio.TimeoutError:
            logger.error(f"Webhook timed out: {url}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
    
    def send_task_complete(self, url: str, task_id: str, result: Dict[str, Any]):
        """Send task completion notification."""
        payload = {
            "event": "task_complete",
            "task_id": task_id,
            "status": "completed",
            "result": result
        }
        asyncio.create_task(self.send(url, payload))
    
    def send_task_failed(self, url: str, task_id: str, error: str):
        """Send task failure notification."""
        payload = {
            "event": "task_failed",
            "task_id": task_id,
            "status": "failed",
            "error": error
        }
        asyncio.create_task(self.send(url, payload))
    
    def send_progress(self, url: str, task_id: str, progress: int, message: str):
        """Send progress update."""
        payload = {
            "event": "task_progress",
            "task_id": task_id,
            "progress": progress,
            "message": message
        }
        asyncio.create_task(self.send(url, payload))

webhook_service = WebhookService()
