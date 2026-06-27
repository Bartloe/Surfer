#src/app/crawler/search/search_manager.py 

from ddgs import DDGS   # <-- nieuwe import

class SearchManager:
    def __init__(self):
        pass

    def search(self, query: str, max_results: int = 10) -> dict:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", ""),
                    "link": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
            return {
                "results": formatted,
                "engine": "duckduckgo",
                "fallback_used": False,
                "fallback_reason": None
            }
        except Exception as e:
            return {
                "results": [],
                "engine": "duckduckgo",
                "fallback_used": True,
                "fallback_reason": str(e)
            }