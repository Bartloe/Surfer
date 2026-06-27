"""
config — alle invoer van Surfer, van buitenaf aan te reiken.

Versie: 1.0
Reden:  Fase 0 — invoer injecteerbaar maken i.p.v. hardcoded / uit een db.
Datum:  2026-06-27 17:56 (NL)

- SurferConfig bundelt álle invoer die een run nodig heeft.
- Een afnemer vult deze velden zelf en geeft ze mee;
  Surfer leest nooit zelf in een afnemer-bestand.
- standaard_config() levert neutrale Surfer-eigen defaults voor een
  zelfstandige run (géén smaak-getunede termen — die hoort de afnemer
  te injecteren).
- De DeepSeek-sleutel komt uit de omgeving (.env), niet uit broncode.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Neutrale defaults — bewust niet smaak-getuned.
STANDAARD_ZOEKTERMEN = [
    "best new tv series 2026",
    "new tv shows 2026",
    "upcoming series 2026",
]

STANDAARD_TALEN = ["nl", "en", "fr", "es", "de", "it", "pt", "sv", "no", "da"]

STANDAARD_VERBODEN_DOMEINEN = [
    "facebook.com", "instagram.com", "tiktok.com", "twitter.com", "x.com",
    "linkedin.com", "pinterest.com", "reddit.com", "youtube.com", "youtu.be",
    "tumblr.com", "threads.net", "twitch.tv", "vimeo.com", "quora.com",
    "bluesky.social", "mastodon.social", "snapchat.com", "discord.com",
]


@dataclass
class SurferConfig:
    zoektermen: list[str]
    profiel_tekst: str = ""
    uitsluitingen: list[str] = field(default_factory=list)
    talen: list[str] = field(default_factory=lambda: list(STANDAARD_TALEN))
    verboden_domeinen: list[str] = field(
        default_factory=lambda: list(STANDAARD_VERBODEN_DOMEINEN)
    )
    max_resultaten_per_term: int = 10
    db_pad: Path = Path("surfer_state.db")
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    min_tekst_voor_taaldetectie: int = 30
    pauze_seconden: float = 1.0

    def __post_init__(self):
        self.db_pad = Path(self.db_pad)
        if not self.deepseek_api_key:
            self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")


def standaard_config(**overrides) -> SurferConfig:
    """Surfer-eigen defaults voor een zelfstandige run; overrides winnen."""
    load_dotenv()
    basis = dict(zoektermen=list(STANDAARD_ZOEKTERMEN))
    basis.update(overrides)
    return SurferConfig(**basis)
