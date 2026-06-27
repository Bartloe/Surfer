import time
import asyncio
import os
from dotenv import load_dotenv
from langdetect import detect

from src.app.services.db_sync import (
    get_active_profile,
    get_search_terms,
    save_discovery_result,
    save_failed_scrape
)
from src.app.crawler.search.search_manager import SearchManager
from src.app.crawler.scrape.scraper import Scraper
from src.app.crawler.extract.extractor import Extractor
from src.app.crawler.analysis.deepseek_client import DeepSeekClient

load_dotenv()

# ============================================================
# CONFIGURATIE
# ============================================================
TOEGESTANE_TALEN = ["nl", "en", "fr", "es", "de", "it", "pt", "sv", "no", "da"]
MIN_TEKST_LENGTE_TAALDETECTIE = 30

VERBODEN_SOCIAL_DOMAINS = [
    "facebook.com", "instagram.com", "tiktok.com", "twitter.com", "x.com",
    "linkedin.com", "pinterest.com", "reddit.com", "youtube.com", "youtu.be",
    "tumblr.com", "threads.net", "twitch.tv", "vimeo.com", "quora.com",
    "bluesky.social", "mastodon.social", "snapchat.com", "discord.com"
]

POSITIEVE_KEYWORDS = [
    "breaking bad", "ozark", "the bear", "succession",
    "antihero", "psychological", "thriller",
    "dark comedy", "satire", "cynical", "witty",
    "dialogue", "drama", "series", "tv show", "season"
]

NEGATIEVE_KEYWORDS = [
    "anime", "reality", "kardashian", "romance", "romantic",
    "movie", "film", "films", "cinema", "trailer", "tickets"
]

# ============================================================
# RUNNER
# ============================================================
class Runner:
    def __init__(self):
        self.profile = None
        self.search_manager = SearchManager()
        self.scraper = Scraper()
        self.extractor = Extractor()
        self.deepseek = None

    def load_profile(self):
        self.profile = get_active_profile()
        if not self.profile:
            raise Exception("Geen actief profiel gevonden.")
        
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_key:
            raise Exception("DeepSeek API key niet gevonden in .env")
        
        self.deepseek = DeepSeekClient(api_key=deepseek_key)

    def _is_allowed_language(self, text):
        if len(text) < MIN_TEKST_LENGTE_TAALDETECTIE:
            return False
        try:
            lang = detect(text)
            return lang in TOEGESTANE_TALEN
        except:
            return True

    def _adjust_match_score(self, match_score, title, snippet):
        text = (title or "") + " " + (snippet or "")
        text_lower = text.lower()
        pos_count = sum(1 for kw in POSITIEVE_KEYWORDS if kw in text_lower)
        neg_count = sum(1 for kw in NEGATIEVE_KEYWORDS if kw in text_lower)
        adjustment = (pos_count * 0.5) - (neg_count * 0.5)
        adjustment = max(-2, min(2, adjustment))
        new_score = match_score + adjustment
        return max(0, min(10, new_score))

    def run(self, max_results=10):
        print(f"\n[Runner] Start crawler met max {max_results} resultaten per zoekterm…")
        self.load_profile()
        search_terms = get_search_terms(self.profile["id"])
        if not search_terms:
            print("[Runner] Geen zoektermen gevonden.")
            return

        print(f"[Runner] Profiel geladen: {self.profile['name']}")
        print(f"[Runner] Aantal zoektermen: {len(search_terms)}\n")

        for term in search_terms:
            print(f"[Runner] Verwerken zoekterm: '{term}'")
            search_result = self.search_manager.search(term, max_results=max_results)
            results = search_result["results"]
            engine = search_result["engine"]
            fallback_used = search_result["fallback_used"]
            fallback_reason = search_result["fallback_reason"]

            print(f"[Runner] Engine: {engine}, fallback: {fallback_used}, reason: {fallback_reason}")

            for r in results:
                url = r.get("link")
                title = r.get("title")
                snippet = r.get("snippet")
                if not url:
                    continue

                if any(domain in url for domain in VERBODEN_SOCIAL_DOMAINS):
                    print(f"[Runner] Overgeslagen (social domain): {url}")
                    continue

                html, scrape_error = self.scraper.fetch(url)
                if scrape_error:
                    save_failed_scrape(
                        url=url,
                        reason=f"Scrape fout: {scrape_error}",
                        engine=engine,
                        profile_id=self.profile["id"]
                    )
                    continue

                extracted = self.extractor.extract(html)
                page_text = getattr(extracted, "text", "")
                description = getattr(extracted, "description", "")
                metadata = getattr(extracted, "metadata", {})

                if not self._is_allowed_language(page_text):
                    print(f"[Runner] Overgeslagen (taal niet toegestaan): {url}")
                    continue

                try:
                    analysis = asyncio.run(
                        self.deepseek.analyze(
                            title=title,
                            text=page_text,
                            description=description,
                            metadata=metadata
                        )
                    )
                except Exception as e:
                    save_failed_scrape(
                        url=url,
                        reason=f"DeepSeek fout: {str(e)}",
                        engine=engine,
                        profile_id=self.profile["id"]
                    )
                    continue

                summary = analysis.get("summary", "")
                match_score = analysis.get("match_score", 0.0)
                relevance_score = analysis.get("relevance_score", 0.0)

                match_score = self._adjust_match_score(match_score, title, snippet)

                save_discovery_result(
                    url=url,
                    title=title,
                    snippet=snippet,
                    summary=summary,
                    match_score=match_score,
                    relevance_score=relevance_score,
                    engine=engine,
                    profile_id=self.profile["id"]
                )

                time.sleep(2)

            time.sleep(2)

        print("\n[Runner] Crawler klaar.\n")