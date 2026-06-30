"""
graafwerk — de web-laag van de stand-alone Surfer-app.

Versie: 1.2
Reden:  Titels uit de omgeving — op tabelpagina's (bv. Ziggo: wedstrijd | tijd |
        'YouTube'-knop) staat de titel in een náástliggende cel, niet in de link.
        Nu wordt die rij/omgeving gebruikt; "YouTube"/"Vimeo"-labels tellen niet
        meer als titel.
Datum:  2026-06-30 21:20 (NL)

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

# Labels die geen echte titel zijn (een afspeel-knopje heet vaak gewoon "video",
# en een verwijzing naar de bron heet vaak gewoon "YouTube"/"Vimeo").
_GENERIEKE_LABELS = {
    "", "video", "video's", "videos", "bekijk video", "bekijk", "speel af",
    "afspelen", "play", "watch", "kijk", "kijken", "lees meer", "meer",
    "youtube", "youtu.be", "vimeo", "dailymotion", "samenvatting",
    "link", "hier", "klik hier", "open", "download", "bron",
}


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
        titel = (titel or "").strip()
        if titel.lower() in _GENERIEKE_LABELS:
            titel = ""                       # "video"-achtige labels niet als titel tonen
        if net not in gevonden:
            gevonden[net] = Treffer(url=net, titel=titel or net, is_video=True)

    for tag in boom.css("iframe"):
        voeg_toe(tag.attributes.get("src", ""), tag.attributes.get("title", ""))
    for tag in boom.css("video source"):
        voeg_toe(tag.attributes.get("src", ""))
    for tag in boom.css("video"):
        voeg_toe(tag.attributes.get("src", ""))
    for tag in boom.css("a"):
        voeg_toe(tag.attributes.get("href", ""), _beste_link_titel(tag))
    og = boom.css_first("meta[property='og:video']") or boom.css_first("meta[property='og:video:url']")
    if og:
        voeg_toe(og.attributes.get("content", ""))

    return list(gevonden.values())


def _beste_link_titel(tag) -> str:
    """De best beschikbare titel van een video-link: rijke sites zetten de echte
    omschrijving vaak in aria-label/title (de zichtbare tekst is dan 'video').
    Volgorde: aria-label -> title -> linktekst -> alt/title van een plaatje erin."""
    kandidaten = [
        tag.attributes.get("aria-label", ""),
        tag.attributes.get("title", ""),
        tag.text() or "",
    ]
    img = tag.css_first("img")
    if img:
        kandidaten += [img.attributes.get("alt", ""), img.attributes.get("title", "")]
    for kandidaat in kandidaten:
        schoon = " ".join((kandidaat or "").split())          # witruimte normaliseren
        if schoon and schoon.lower() not in _GENERIEKE_LABELS:
            return schoon
    return _titel_uit_omgeving(tag)


def _titel_uit_omgeving(tag) -> str:
    """Geen bruikbare titel in de link zelf? Haal hem uit de directe omgeving.
    Tabelpagina's (bv. Ziggo) zetten een 'YouTube'-knop náást de echte titel in
    dezelfde rij; anders staat de titel in een kop/onderschrift van het blok."""
    rij = _opwaarts(tag, "tr")
    if rij is not None:
        delen = []
        for cel in rij.css("td, th"):
            t = " ".join((cel.text() or "").split())
            if t and t.lower() not in _GENERIEKE_LABELS and t not in delen:
                delen.append(t)
        if delen:
            return " — ".join(delen)[:160]
    blok = _opwaarts(tag, ("figure", "article", "li"))
    if blok is not None:
        kop = blok.css_first("figcaption, h1, h2, h3, h4, h5, h6")
        if kop:
            t = " ".join((kop.text() or "").split())
            if t and t.lower() not in _GENERIEKE_LABELS:
                return t[:160]
    return ""


def _opwaarts(tag, namen):
    """Dichtstbijzijnde ouder met (een van) deze tag-namen; None als die er niet is."""
    if isinstance(namen, str):
        namen = (namen,)
    node = tag.parent
    for _ in range(8):                          # nooit eindeloos omhoog klimmen
        if node is None:
            return None
        if node.tag in namen:
            return node
        node = node.parent
    return None


def _normaliseer(url: str) -> str:
    """YouTube embed / youtu.be terugbrengen naar een gewone, klikbare watch-url."""
    m = re.search(r"(?:youtube(?:-nocookie)?\.com/embed/|youtu\.be/)([\w\-]{6,})", url)
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}"
    return url
