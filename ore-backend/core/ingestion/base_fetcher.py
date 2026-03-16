from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import asyncio
import aiohttp

class BaseFetcher(ABC):
    """Abstract base class for all data fetchers."""
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the data source."""
        pass
    
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for papers/documents."""
        pass
    
    @abstractmethod
    def fetch_metadata(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Fetch metadata for a specific document."""
        pass
    
    async def download_content(self, url: str, dest_path: str) -> bool:
        """Download content from URL to destination path."""
        retries = 3
        backoff = 0.5
        
        for attempt in range(1, retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.read()
                            with open(dest_path, "wb") as f:
                                f.write(content)
                            return True
            except Exception as e:
                if attempt < retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2
        return False
