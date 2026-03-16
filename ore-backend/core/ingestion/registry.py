from typing import Dict, List, Optional
from core.ingestion.base_fetcher import BaseFetcher
from core.ingestion.fetchers import ArxivFetcher

class FetcherRegistry:
    """Registry for managing multiple data fetchers."""
    
    def __init__(self):
        self._fetchers: Dict[str, BaseFetcher] = {}
        self._register_default_fetchers()
    
    def _register_default_fetchers(self):
        """Register default fetchers."""
        self.register(ArxivFetcher())
    
    def register(self, fetcher: BaseFetcher):
        """Register a new fetcher."""
        self._fetchers[fetcher.source_name] = fetcher
    
    def get(self, source: str) -> Optional[BaseFetcher]:
        """Get a fetcher by source name."""
        return self._fetchers.get(source)
    
    def list_sources(self) -> List[str]:
        """List all available sources."""
        return list(self._fetchers.keys())
    
    def search(self, source: str, query: str, max_results: int = 10):
        """Search using a specific fetcher."""
        fetcher = self.get(source)
        if not fetcher:
            raise ValueError(f"Unknown source: {source}")
        return fetcher.search(query, max_results)
    
    def fetch_metadata(self, source: str, identifier: str):
        """Fetch metadata from a specific source."""
        fetcher = self.get(source)
        if not fetcher:
            raise ValueError(f"Unknown source: {source}")
        return fetcher.fetch_metadata(identifier)

fetcher_registry = FetcherRegistry()
