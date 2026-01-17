import arxiv
import os
import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from config import settings
import time

class ArxivFetcher:
    def __init__(self):
        self.client = arxiv.Client()

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Searches ArXiv for papers.
        """
        # Note: arxiv library handles its own retries, but we wrap it just in case
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
                    "arxiv_id": r.get_short_id()
                })
        except Exception as e:
            print(f"ArXiv search failed: {e}")
            return []

        return results

    async def download_pdf(self, url: str, paper_id: str) -> Optional[str]:
        """
        Downloads PDF asynchronously with retry logic.
        """
        filename = f"{paper_id}.pdf"
        filepath = os.path.join(settings.RAW_DIR, filename)

        if os.path.exists(filepath):
            return filepath

        retries = 3 # 3 Retries means 4 total attempts
        backoff = 0.5

        for attempt in range(1, retries + 2): # 1 to 4
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.read()
                            with open(filepath, "wb") as f:
                                f.write(content)
                            return filepath
                        else:
                            print(f"Attempt {attempt} failed: HTTP {response.status}")
            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")

            if attempt < retries + 1:
                print(f"Retrying ingestion in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2

        print(f"Failed to download {url} after {retries + 1} attempts.")
        return None
