"""
scrapen — pagina ophalen.

Versie: 1.0
Reden:  Fase 0 — eenvoudige, eerlijke fetch; headless/Playwright verwijderd.
Datum:  2026-06-27 17:56 (NL)

- haal_op() geeft (html, fout): bij succes html + None, bij fout None + reden.
- Zwakste schakel van de keten; bewust geïsoleerd zodat hij later los te
  harden is (retry/anti-bot) zonder de rest te raken.
"""

import requests

STANDAARD_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class Scraper:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.sessie = requests.Session()
        self.sessie.headers.update({"User-Agent": STANDAARD_USER_AGENT})

    def haal_op(self, url: str):
        try:
            antwoord = self.sessie.get(url, timeout=self.timeout)
            antwoord.raise_for_status()
            return antwoord.text, None
        except Exception as e:
            return None, str(e)
