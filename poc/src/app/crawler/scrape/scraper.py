#src/app/crawler/scrape/scraper.py
import requests

class Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def fetch(self, url: str):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text, None
        except Exception as e:
            return None, str(e)