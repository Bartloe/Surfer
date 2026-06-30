"""
graafwerk — de web-laag van de stand-alone Surfer-app.

Versie: 1.0
Reden:  Eerste versie — video-gericht zoeken bovenop het GEDEELDE Surfer-graafwerk.
Datum:  2026-06-30 19:18 (NL)

- Hergebruikt ONGEWIJZIGD het graafwerk van de bestaande Surfer (../poc):
  Scraper.haal_op (pagina ophalen) en extraheer (leesbare tekst).
- zoek_videos / zoek_paginas: video-gericht zoeken via DuckDuckGo (ddgs).
- haal_pagina: één pagina ophalen + tekst eruit (voor het DeepSeek-oordeel).
- videos_op_pagina: alle video-urls die OP een pagina staan (meerdere per pagina).
- Past GEEN content-/domeinfilters toe: alle sites zijn bereikbaar.
- Faalt overal zacht: bij een fout een lege lijst / nette foutmelding, nooit een crash.
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

# --- het GEDEELDE graafwerk van de bestaande Surfer (poc) — niet wijzigen ------
_SURFER_POC = Path(__file__).resolve().parent.parent / "poc"
if str(_SURFER_POC) not in sys.path:
    sys.path.insert(0, str(_SURFER_POC))
from surfer.scrapen import Scraper          # pagina ophalen (gedeeld)
from surfer.extractie import extraheer      # leesbare tekst uit HTML (gedeeld)

from ddgs import DDGS
from selectolax.parser import HTMLParser


@dataclass
class Treffer:
    """Eén ruwe zoektreffer (vóór het DeepSeek-oordeel)."""
    url: str
    titel: str
    fragment: str = ""        # korte beschrijving van de zoekmachine/pagina
    is_video: bool = True


_VIDEO_HINTS = (
    "youtube.com/watch", "youtu.be/", "youtube.com/embed", "youtube-nocookie.com",
    "player.vimeo.com", "vimeo.com/", "dailymotion.com/video", "dailymotion.com/embed",
    ".mp4", ".webm",
)

_scraper = Scraper()


def zoek_videos(term: str, max_resultaten: int = 15) -> list[Treffer]:
    """Rechtstreeks op video's zoeken (YouTube/Vimeo/etc.)."""
    try:
        with DDGS() as ddgs:
            ruw = list(ddgs.videos(term, max_results=max_resultaten))
    except Exception:
        return []
    treffers = []
    for r in ruw:
        url = (r.get("content") or r.get("embed_url") or "").strip()
        if not url:
            continue
        treffers.append(Treffer(
            url=url,
            titel=(r.get("title") or "").strip() or url,
            fragment=(r.get("description") or "").strip(),
            is_video=True,
        ))
    return treffers


def zoek_paginas(term: str, max_resultaten: int = 15) -> list[Treffer]:
    """Gewone webpagina's zoeken (om er video's vanaf te halen)."""
    try:
        with DDGS() as ddgs:
            ruw = list(ddgs.text(term, max_results=max_resultaten))
    except Exception:
        return []
    treffers = []
    for r in ruw:
        url = (r.get("href") or "").strip()
        if not url:
            continue
        treffers.append(Treffer(
            url=url,
            titel=(r.get("title") or "").strip() or url,
            fragment=(r.get("body") or "").strip(),
            is_video=False,
        ))
    return treffers


def haal_pagina(url: str) -> dict:
    """Eén pagina ophalen + tekst extraheren. Geeft {html, titel, tekst, fout}."""
    html, fout = _scraper.haal_op(url)
    if fout:
        return {"html": None, "titel": "", "tekst": "", "fout": f"ophalen: {fout}"}
    extractie = extraheer(html)
    if extractie is None:
        return {"html": html, "titel": "", "tekst": "", "fout": "geen bruikbare tekst"}
    return {"html": html, "titel": extractie.titel, "tekst": extractie.tekst, "fout": None}


def videos_op_pagina(html: str, basis_url: str = "") -> list[Treffer]:
    """Alle video-urls die OP deze pagina staan (iframe/video/links). Meerdere per pagina."""
    if not html:
        return []
    gevonden: dict[str, Treffer] = {}
    boom = HTMLParser(html)

    def voeg_toe(url: str, titel: str = ""):
        url = (url or "").strip()
        if not url or not any(h in url.lower() for h in _VIDEO_HINTS):
            return
        net = _normaliseer(url)
        if net not in gevonden:
            gevonden[net] = Treffer(url=net, titel=titel.strip() or net, is_video=True)

    for tag in boom.css("iframe"):
        voeg_toe(tag.attributes.get("src", ""))
    for tag in boom.css("video source"):
        voeg_toe(tag.attributes.get("src", ""))
    for tag in boom.css("video"):
        voeg_toe(tag.attributes.get("src", ""))
    for tag in boom.css("a"):
        voeg_toe(tag.attributes.get("href", ""), tag.text())
    og = boom.css_first("meta[property='og:video']") or boom.css_first("meta[property='og:video:url']")
    if og:
        voeg_toe(og.attributes.get("content", ""))

    return list(gevonden.values())


def _normaliseer(url: str) -> str:
    """YouTube embed / youtu.be terugbrengen naar een gewone, klikbare watch-url."""
    m = re.search(r"(?:youtube(?:-nocookie)?\.com/embed/|youtu\.be/)([\w\-]{6,})", url)
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}"
    return url
