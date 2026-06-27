import httpx
from selectolax.parser import HTMLParser
from typing import List, Dict


class GoogleHTMLSearch:
    """
    HTML fallback search engine.
    Used when Brave API returns no results or fails.
    """

    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        q = query.replace(" ", "+")
        url = f"https://www.google.com/search?q={q}"

        async with httpx.AsyncClient(
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SurferBot/1.0)"}
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        html = HTMLParser(response.text)
        results = []

        for block in html.css("div.g"):
            link = block.css_first("a")
            title = block.css_first("h3")
            snippet = block.css_first(".VwiC3b")

            if not link or not title:
                continue

            results.append({
                "url": link.attributes.get("href"),
                "title": title.text(),
                "snippet": snippet.text() if snippet else "",
                "engine": "google_html"
            })

            if len(results) >= num_results:
                break

        return results
