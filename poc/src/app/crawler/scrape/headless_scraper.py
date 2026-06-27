from playwright.async_api import async_playwright
from typing import Optional


class HeadlessScraper:
    """
    Headless browser fallback for pages blocked by anti-bot or requiring JS.
    """

    async def fetch(self, url: str) -> Optional[str]:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(url, timeout=15000)

                # Wait for content
                await page.wait_for_timeout(1500)

                html = await page.content()
                await browser.close()

                if len(html.strip()) < 50:
                    return None

                return html

        except Exception:
            return None
