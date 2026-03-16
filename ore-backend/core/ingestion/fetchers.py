import arxiv
import os
import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from config import settings
from core.ingestion.base_fetcher import BaseFetcher
import time

class ArxivFetcher(BaseFetcher):
    def __init__(self):
        self.client = arxiv.Client()
    
    @property
    def source_name(self) -> str:
        return "arxiv"
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        results = []
        try:
            for r in self.client.results(search):
                results.append({
                    "title": r.title,
                    "authors": [a.name for a in r.authors],
                    "abstract": r.summary,
                    "doi": r.doi,
                    "url": r.entry_id,
                    "pdf_url": r.pdf_url,
                    "published_date": r.published,
                    "source": "arxiv",
                    "identifier": r.get_short_id()
                })
        except Exception as e:
            print(f"ArXiv search failed: {e}")
            return []

        return results

    def fetch_metadata(self, identifier: str) -> Optional[Dict]:
        try:
            search = arxiv.Search(id_list=[identifier])
            for r in self.client.results(search):
                return {
                    "title": r.title,
                    "authors": [a.name for a in r.authors],
                    "abstract": r.summary,
                    "doi": r.doi,
                    "url": r.entry_id,
                    "pdf_url": r.pdf_url,
                    "published_date": r.published,
                    "source": "arxiv",
                    "identifier": r.get_short_id()
                }
        except Exception as e:
            print(f"ArXiv fetch failed: {e}")
        return None

    async def download_pdf(self, url: str, paper_id: str) -> Optional[str]:
        filename = f"{paper_id}.pdf"
        filepath = os.path.join(settings.RAW_DIR, filename)

        if os.path.exists(filepath):
            return filepath

        return await self.download_content(url, filepath)
