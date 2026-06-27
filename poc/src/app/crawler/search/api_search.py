import httpx
from typing import List, Dict


class BraveSearchAPI:
    """
    Primary search engine using Brave Search API.
    Falls back to HTML search if needed (handled by SearchManager).
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        headers = {"X-Subscription-Token": self.api_key}
        params = {"q": query, "count": num_results}

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self.url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "url": item.get("url"),
                "title": item.get("title", ""),
                "snippet": item.get("description", ""),
                "engine": "brave_api"
            })

        return results
